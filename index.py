from dash import html, callback_context
from dash.dependencies import Input, Output
import dash
from dash import dcc
import plotly.express as px
from json import dumps
import numpy as np
import dash_bootstrap_components as dbc
import pandas as pd
import sqlalchemy as salc
from app import app
from app import server

# import page files from project.
from pages import start, overview, cicd

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format("augur", "OFaccess21", "sandiego.osci.io", 6432, "sandiego")

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})

pr_query = salc.sql.text(f"""
    SET SCHEMA 'augur_data';
        SELECT DISTINCT
            r.repo_git,
            rg.rg_name 
        FROM
            repo r
        JOIN repo_groups rg
        ON rg.repo_group_id = r.repo_group_id
        ORDER BY rg.rg_name
        """)
df_search_bar = pd.read_sql(pr_query, con=engine)

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

    ], align="center", justify="center"),

    # the displayed data should be below the search bar and the buttons.
    dbc.Row([
        html.Div(id='display-page')
    ]),

    dbc.Row([
            html.Footer("Report issues to jkunstle@redhat.com, topic: Explorer Issue",
                   style={"textDecoration": "underline"})

        ], align='end' )


])



"""
    Page Callbacks
"""
@app.callback(
    Output('display-page', 'children'),
    Input('start-page', 'n_clicks'),
    Input('overview-page', 'n_clicks'),
    Input('cicd-page', 'n_clicks')
)

def return_template(_start, _overview, _cicd):
    ctx = callback_context
    caller = ctx.triggered[0]["prop_id"]

    # default caller on first execution.
    if caller == ".":
        return start.layout
    else:
        call_name = caller.split(".")[0]
        name_dict = {
            "start-page": start.layout,
            "overview-page": overview.layout,
            "cicd-page": cicd.layout
        }
        return name_dict[call_name]

@app.callback(
    Output('results-output-container', 'children'),
    Input('projects', 'value')
)
def update_output(value):
    repo_git_set = []
    org_name_set = []
    repo_ids= []
    repo_names = []
    org_repo_ids= []
    org_repo_names = []

    for r in value: 
        if r.startswith('http'):
            repo_git_set.append(r)
        else: 
            org_name_set.append(r)

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

    total_ids = set(repo_ids + org_repo_ids)
    total_names = set(repo_names + org_repo_names) 

    return f'You have selected {value}, repo ids {total_ids}, with repo names {total_names}'



if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
