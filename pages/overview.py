from turtle import title
from dash import html, callback_context, callback, dcc
import plotly.express as px
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
from app import app
import pandas as pd
from .visualizations import commits_activity as ca

"""
    TODO: How can we pass the repo-list to the layout
            and still have callbacks for graph updates?

            Call-backs fire when the UI element that they're 
            bound to changes state so we might not need to worry about that.
"""

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1(children="Overview Page - live update!")
            ]
        )
        ]
    ),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='commits-over-time')
            ]
        )
        ]
    ),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='issues-over-time')
            ]
        )
        ]
    ),

])

    
@callback(
    Output('commits-over-time', 'figure'),
    Input('commits-data', 'data')
)
def create_commits_over_time_graph(data):
    df_commits = pd.DataFrame(data)

    # reset index to be ready for plotly
    df_commits = df_commits.reset_index()
    if(df_commits is not None):
        fig = px.bar(df_commits, x="date", y="index")
        return fig
    else:
        return None
    
@callback(
    Output('issues-over-time', 'figure'),
    Input('issues-data', 'data')
)
def create_commits_over_time_graph(data):
    df_issues = pd.DataFrame(data)

    # drop null values, sort them by creation date,
    # and reset the index.
    df_issues = df_issues[df_issues['pull_request_id'].isnull()]
    df_issues = df_issues.drop(columns = 'pull_request_id' )
    df_issues = df_issues.sort_values(by= "created")
    df_issues = df_issues.reset_index(drop=True)

    # created dataframe 
    df_created = pd.DataFrame(df_issues["created"])
    df_created["issue"] = df_created["created"]
    df_created['open'] = 1
    df_created = df_created.drop(columns="created")
    
    # closed dataframe
    df_closed = pd.DataFrame(df_issues["closed"]).dropna()
    df_closed["issue"] = df_closed["closed"]
    df_closed['open'] = -1
    df_closed = df_closed.drop(columns= "closed")

    # open dataframe 
    df_open = pd.concat([df_created, df_closed])
    df_open = df_open.sort_values("issue")
    df_open = df_open.reset_index(drop=True)
    df_open["total"] = df_open["open"].cumsum()

    # make sure that the values are Datetime so that the following conversion works.
    df_open["issue"] = pd.to_datetime(df_open['issue'])
    df_open['issue'] = df_open['issue'].dt.floor("D")

    # edit open dataframe
    df_open = pd.concat([df_created, df_closed])
    df_open = df_open.sort_values("issue")
    df_open = df_open.reset_index(drop=True)
    df_open["total"] = df_open["open"].cumsum()
    #df_open['issue'] = df_open['issue'].apply(lambda x: x.replace(hour = 0, minute=0, second=0))
    df_open = df_open.drop_duplicates(subset='issue', keep='last')
    df_open = df_open.drop(columns= 'open')

    # reset index to be ready for plotly
    if(df_open is not None):
        fig = px.line(df_open, x="issue", y="total", title='# Issues Open')
        return fig
    else:
        return None