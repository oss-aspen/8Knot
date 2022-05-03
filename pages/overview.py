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

])

    
@callback(
    Output('commits-over-time', 'figure'),
    Input('commits-data', 'data')
)
def create_graph(data):
    df_commits = pd.DataFrame(data)

    # reset index to be ready for plotly
    df_commits = df_commits.reset_index()
    if(df_commits is not None):
        fig = px.bar(df_commits, x="date", y="index")
        return fig
    else:
        return None
    