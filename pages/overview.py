from dash import html, dcc
import plotly.express as px
from dash.dependencies import Input, Output

from app import app
from .visualizations import commits_activity as ca

layout = html.Div(children=[
    html.H1(children="Overview Page!"),
    dcc.Graph(id='commits-over-time')
])

@app.callback(
    Output('commits-over-time', 'figure'),
    Input('commits-over-time', 'value')
)
def graph_commits_over_time(value):
    commits_df = ca.ret_df('augur')
    print(commits_df.head())
    fig = px.line(
        commits_df,
        x="date_time",
        y="count",
        title=f"Number of weekly commits for Augur repo"
    )
    return fig