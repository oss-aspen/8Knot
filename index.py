from cProfile import label
from cgitb import small
from dash import html, callback_context, callback
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

pr_query = f"""SELECT * FROM augur_data.explorer_entry_list"""

df_search_bar = augur_db.run_query(pr_query)

entries = np.concatenate(( df_search_bar.rg_name.unique() , df_search_bar.repo_git.unique() ), axis=None)
entries = entries.tolist()


sidebar = html.Div(
    [
        html.H2("Pages", className="display-10"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Overview Page", href='/overview', active="exact"),
                dbc.NavLink("CI/CD Page", href='/cicd', active="exact"),
            ],
        vertical=True,
        pills=True,
        ),
    ]
)


index_layout = dbc.Container([
    # we need to pass our repository choices to our graphs after they are chosen
    # in our search bar. This is how we can store our choices, and this is updated
    # when we change our search parameters with the search bar.
    dcc.Store(id= "repo_choices", storage_type="session", data=[]),
    dcc.Store(id='commits-data', data=[], storage_type='session'),
    dcc.Location(id="url"), 

    
    dbc.Row([

        dbc.Col(sidebar, width= 2),
        
        dbc.Col([
            html.H1("Sandiego Explorer Demo Multipage",className='text-center'),
            html.Label("Select Github repos or orgs:"),
            html.Div([
                html.Div(
                    [dcc.Dropdown(id='projects', multi=True, value=['agroal'],
                         options=[{'label':x, 'value':x}
                                  for x in sorted(entries)])
                    ],style={"width": "50%",'display':'table-cell','verticalAlign': 'middle',"padding-right": "10px"} 
                ),
                dbc.Button("Search", id="search", n_clicks=0, class_name = 'btn btn-primary',
                            style={'verticalAlign': 'top','display':'table-cell'})
                ],style={'display':'table', 'width':'75%', "padding": "10px"}
            ),
            html.Div(id='display-page', children=[]),
        
        ],width={"size": 8, "offset": 1}

        ),

    ],justify="start"),

    dbc.Row([dbc.Col([
        html.Footer("Report issues to jkunstle@redhat.com, topic: Explorer Issue",
                   style={"textDecoration": "underline"})],width={"offset":8})
    ],)

],fluid= True,style = {"padding-top": "1em"}, 
)

app.layout = index_layout

    # html.Div([
    # sidebar,
    # index_layout])

### Assemble all layouts ###
app.validation_layout = html.Div(
    children = 
    [
        #sidebar,
        index_layout,
        start.layout,
        overview.layout,
        cicd.layout
    ]
)

"""
    Page Callbacks
"""
@callback(
    Output('display-page', 'children'),
    Input('url', 'pathname')
)

def display_page(pathname):
    if pathname == '/overview':
        return overview.layout
    elif pathname == '/cicd':
        return cicd.layout
    elif pathname == '/':
        return start.layout
    else: 
        return '404'
 
def _parse_repo_choices( repo_git_set ):

    repo_ids= []
    repo_names = []

    if len(repo_git_set) > 0:
        url_query = str(repo_git_set)
        url_query = url_query[1:-1]

        repo_query = salc.sql.text(f"""
        SET SCHEMA 'augur_data';
        SELECT DISTINCT
            r.repo_id,
            r.repo_name
        FROM
            repo r
        JOIN repo_groups rg 
        ON r.repo_group_id = rg.repo_group_id
        WHERE
            r.repo_git in({url_query})
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
        name_query = str(org_name_set)
        name_query = name_query[1:-1]

        org_query = salc.sql.text(f"""
        SET SCHEMA 'augur_data';
        SELECT DISTINCT
            r.repo_id,
            r.repo_name
        FROM
            repo r
        JOIN repo_groups rg 
        ON r.repo_group_id = rg.repo_group_id
        WHERE
            rg.rg_name in({name_query})
        """)


        t = engine.execute(org_query)
        results = t.all()
        org_repo_ids = [ row[0] for row in results]
        org_repo_names = [ row[1] for row in results]

    return org_repo_ids, org_repo_names


@app.callback(
    Output('repo_choices', 'data'),
    Input('search', 'n_clicks'),
    State('projects', 'value')
)
def update_output(n_clicks, value):

    """
        Section handles parsing the input repos / orgs when there is selected values
    """
    print("testing")
    if len(value) > 0:
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
        total_ids = list(total_ids)

        # return the string that we want and return the list of the id's that we need for the other callback.
        return total_ids
    elif len(value) == 0:
        raise dash.exceptions.PreventUpdate

@callback(
    Output('commits-data','data'),
    Input('repo_choices', 'data')
)
def generate_commit_data(repo_ids):
    print("commits query start")
    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    commits_query = salc.sql.text(f"""
                    SELECT
                        r.repo_name,
                        c.cmt_commit_hash AS commits,
                        c.cmt_id AS file, 
                        c.cmt_added AS lines_added,
                        c.cmt_removed AS lines_removed,
                        c.cmt_author_date AS date
                    FROM
                        repo r
                    JOIN commits c 
                    ON r.repo_id = c.repo_id
                    WHERE
                        c.repo_id in({repo_statement})
                    """)
    df_commits = pd.read_sql(commits_query, con=engine)

    df_commits = df_commits.reset_index()
    df_commits.drop("index", axis=1, inplace=True)
    print("commits query complete")
    return df_commits.to_dict('records')


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
