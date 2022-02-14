from turtle import title
from dash import html, dcc
import plotly.express as px
from dash.dependencies import Input, Output
import plotly.express as px

from app import app
from .visualizations import commits_activity as ca

"""
    TODO: How can we pass the repo-list to the layout
            and still have callbacks for graph updates?

            Call-backs fire when the UI element that they're 
            bound to changes state so we might not need to worry about that.
"""

def get_layout(repos: list):

    print("on overview page, passed repos: " + str(repos))

    commits_over_time_fig = _graph_commits_over_time(repos)

    layout = html.Div(children=[
        html.H1(children="Overview Page - live update!"),
        html.H3(children=f"Selected Repo_ID's: {str(repos)}"),
        dcc.Graph(figure=commits_over_time_fig)
    ])

    return layout


def _graph_commits_over_time(repos: list):

    # TODO (james) come back and fix
    commits_df = 1

    # get dataframe
    # commits_df = ca.ret_df(repos, "copy_cage.json")

    # # overwrite the index name
    # commits_df.index.name = "count"

    # # reset index to be ready for plotly
    # commits_df = commits_df.reset_index()

    # # respecify the names of the columns so that we can use plotly
    # commits_df = commits_df.rename(columns={"count": "time", "date_time": "count"})
    
    if(commits_df is not None):
        #fig = px.bar(commits_df, x="time", y="count")

        # dummy graph that we return
        fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
        #fig = px.scatter(commits_df, x="time", y="count")
        return fig
    else:
        return None
