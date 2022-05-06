from turtle import title
from dash import html, callback_context, callback, dcc
import plotly.express as px
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
from app import app
import pandas as pd
import datetime as dt
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
            dcc.Graph(id='commits-over-time'),
            html.Label(['Date Interval'],style={'font-weight': 'bold'}),
            dcc.RadioItems(
                id='time_interval',
                options=[
                         {'label': 'Day', 'value': 86400000},
                         {'label': 'Week', 'value': 604800000},
                         {'label': 'Month', 'value': 'M1'},
                         {'label': 'Year', 'value': 'M12'}
                ],
                value='M1',
                style={"width": "50%"}
            ),
            ],#style={"width": "50%"}
        )
        ]
    )
], fluid= True)

    
@callback(
    Output('commits-over-time', 'figure'),
    [Input('commits-data', 'data'),
    Input('time_interval','value')]
)
def create_graph(data,interval):
    df_commits = pd.DataFrame(data)

    # reset index to be ready for plotly
    df_commits = df_commits.reset_index()

    today = dt.date.today()
    x_r = []
    if interval == 86400000:
        x_r = [str(today-dt.timedelta(weeks=4)),str(today)]
    elif interval == 604800000:
        x_r = [str(today-dt.timedelta(weeks=30)),str(today)]
    
    if(df_commits is not None):
        fig = px.histogram(df_commits, x="date",range_x=x_r)
        fig.update_traces(xbins_size=interval)
        fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick=interval)
        fig.update_layout(
            title={'text':"Commits Over Time",
                      'font':{'size':28},'x':0.5,'xanchor':'center'},
        xaxis_title="Time",
        yaxis_title="Number of Commits")
        return fig
    else:
        return None  
