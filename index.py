from dash import html, callback_context
from dash.dependencies import Input, Output, State
import dash
from dash import dcc
import plotly.express as px
from json import dumps
import numpy as np
import dash_bootstrap_components as dbc
import pandas as pd
import sqlalchemy as salc
from app import app, server, engine, augur_db
import os

# import page files from project.
from pages import start, overview, cicd

pr_query = f"""
                SELECT DISTINCT
                    r.repo_git,
                    rg.rg_name 
                FROM
                    repo r
                JOIN repo_groups rg
                ON rg.repo_group_id = r.repo_group_id
                ORDER BY rg.rg_name
                """

df_search_bar = augur_db.run_query(pr_query)

entries = np.concatenate(( df_search_bar.rg_name.unique() , df_search_bar.repo_git.unique() ), axis=None)
entries = entries.tolist()


app.layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.H1("Sandiego Explorer Demo Multipage",
                        className='text-center font-weight-bold mb-4')
            ]
        ),
        
        ], align="center", justify="center"),

    dbc.Row([
        dbc.Col([
            html.Div(
                [
                    dbc.Button("Start page", id = "start-page", outline= True, color = 'secondary', n_clicks=0),
                    dbc.Button("Overview Page", id = "overview-page", outline= True, color = 'primary', n_clicks=0),
                    dbc.Button("CI/CD Page", id = "cicd-page", outline= True, color = 'success', n_clicks=0)

                ])
        ])
    ]),

    dbc.Row([

        dbc.Col([
            html.H1("Select Github repos or orgs:",
                        className='text-center font-weight-bold mb-4')
            ],width=12)
    ]),

    dbc.Row([

        dbc.Col([
            dcc.Dropdown(id='projects', multi=True, value=['agroal'],
                         options=[{'label':x, 'value':x}
                                  for x in sorted(entries)],
                          className= 'mb-4'),
            #dcc.Graph(id='line-fig2', figure={})
            html.Div(id='results-output-container',className= 'mb-4')
            ], width={'size':8},
           #xs=12, sm=12, md=12, lg=5, xl=5
        ),
        dbc.Col([
            dbc.Button("Search", id="search", n_clicks=0)
        ])

    ], align="center", justify="center"),

    # the displayed data should be below the search bar and the buttons.
    dbc.Row([
        html.Div(id='display-page', children=[])
    ]),

    dbc.Row([
            html.Footer("Report issues to jkunstle@redhat.com, topic: Explorer Issue",
                   style={"textDecoration": "underline"})

        ], align='end' ),
    
    # we need to pass our repository choices to our graphs after they are chosen
    # in our search bar. This is how we can store our choices, and this is updated
    # when we change our search parameters with the search bar.
    dcc.Store(id="repo_choices", storage_type="session", data=[]),
    dcc.Store(id="prev_page", storage_type="session", data="start")


])

"""
    Page Callbacks
"""
@app.callback(
    [Output('display-page', 'children'),
     Output('prev_page', 'data')],
    [Input('start-page', 'n_clicks'),
     Input('overview-page', 'n_clicks'),
     Input('cicd-page', 'n_clicks'),
     Input('repo_choices', 'data')],
     State('prev_page', "data")
)

def return_template(_start, _overview, _cicd, repo_choices, prev_page):
    ctx = callback_context
    caller = ctx.triggered[0]["prop_id"]

    # default caller on first execution.
    if caller == ".":
        return start.layout, "start"
    else:
        # which of the buttons is triggering this callback?
        call_name = caller.split(".")[0]

        if(call_name == "overview-page"):
            return overview.get_layout(repo_choices), "overview"
        elif(call_name == "start-page"):
            return start.layout, "start"
        elif(call_name == "cicd-page"):
            return cicd.layout, "cicd"
        else:
            if(prev_page == "overview"):
                return overview.get_layout(repo_choices), dash.no_update
            elif(prev_page == "start"):
                return start.layout, dash.no_update
            elif(prev_page == "cicd"):
                return cicd.layout, dash.no_update
            else:
                return start.layout, dash.no_update
 
def _parse_repo_choices( repo_git_set ):

    repo_ids= []
    repo_names = []

    if len(repo_git_set) > 0:
        url_query = 'r.repo_git = '
        for repo_git in repo_git_set:
            url_query+= '\''
            url_query+=repo_git
            url_query+='\' OR\n\t\tr.repo_git = '
            
        url_query = url_query[:-18]

        repo_query = salc.sql.text(f"""
        SET SCHEMA 'augur_data';
        SELECT DISTINCT
            r.repo_id,
            r.repo_name
        FROM
            repo r
        JOIN repo_groups rg ON r.repo_group_id = rg.repo_group_id
        WHERE
            {url_query}
        """)

        t = engine.execute(repo_query)
        results = t.all()
        repo_ids = [ row[0] for row in results]
        repo_names = [ row[1] for row in results]

    return repo_ids, repo_names
    
def _parse_org_choices( org_name_set ):
    org_repo_ids= []
    org_repo_names = []

    if len(org_name_set) > 0:
        name_query = "rg.rg_name = "
        for name in org_name_set:
            name_query+= '\''
            name_query+=name
            name_query+='\' OR\n\t\trg.rg_name = '

        name_query = name_query[:-18]

        org_query = salc.sql.text(f"""
        SET SCHEMA 'augur_data';
        SELECT DISTINCT
            r.repo_id,
            r.repo_name
        FROM
            repo r
        JOIN repo_groups rg ON r.repo_group_id = rg.repo_group_id
        WHERE
            {name_query}
        """)


        t = engine.execute(org_query)
        results = t.all()
        org_repo_ids = [ row[0] for row in results]
        org_repo_names = [ row[1] for row in results]

    return org_repo_ids, org_repo_names


@app.callback(
    [Output('results-output-container', 'children'),
     Output('repo_choices', 'data')],
    Input('search', 'n_clicks'),
    State('projects', 'value')
)
def update_output(n_clicks, value):

    """
        Section handles parsing the input repos / orgs
    """

    repo_git_set = []
    org_name_set = []
    
    # split our processing of repos / orgs into two streams
    for r in value: 
        if r.startswith('http'):
            repo_git_set.append(r)
        else: 
            org_name_set.append(r)

    # get the repo_ids and the repo_names from our repo set of urls'
    repo_ids, repo_names = _parse_repo_choices(repo_git_set=repo_git_set)

    # get the repo_ids and the repo_names from our org set of names
    org_repo_ids, org_repo_names = _parse_org_choices(org_name_set=org_name_set)

    # collect all of the id's and names together
    total_ids = set(repo_ids + org_repo_ids)
    total_names = set(repo_names + org_repo_names) 

    # return the string that we want and return the list of the id's that we need for the other callback.
    return f'You have selected {value}, repo ids {total_ids}, with repo names {total_names}', list(total_ids)



if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
