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

layout = dbc.Container(
    [
        dbc.Row([dbc.Col([html.H1(children="Chaoss WIP Page - live update")])]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id="commits-over-time1"),
                        html.Label(["Date Interval"], style={"font-weight": "bold"}),
                        dcc.RadioItems(
                            id="time_interval",
                            options=[
                                {"label": "Day", "value": 86400000},
                                {"label": "Week", "value": 604800000},
                                {"label": "Month", "value": "M1"},
                                {"label": "Year", "value": "M12"},
                            ],
                            value="M1",
                            style={"width": "50%"},
                        ),
                    ],
                ),
                dbc.Col(
                    [
                        dcc.Graph(id="first-time-contributors"),
                    ],
                ),
            ]
        ),
    ],
    fluid=True,
)

# call back for commits over time graph
@callback(
    Output("commits-over-time1", "figure"),
    [Input("commits-data", "data"), Input("time_interval", "value")],
)
def create_graph(data, interval):
    df_commits = pd.DataFrame(data)

    # reset index to be ready for plotly
    df_commits = df_commits.reset_index()

    # helper values for building graph
    today = dt.date.today()
    x_r = []
    x_name = "Year"
    hover = "Year: %{x|%Y}"

    # graph input values based on date interval selection
    if interval == 86400000:
        x_r = [str(today - dt.timedelta(weeks=4)), str(today)]
        x_name = "Day"
        hover = "Day: %{x|%b %d, %Y}"
    elif interval == 604800000:
        x_r = [str(today - dt.timedelta(weeks=30)), str(today)]
        x_name = "Week"
        hover = "Week: %{x|%b %d, %Y}"
    elif interval == "M1":
        x_r = [str(today - dt.timedelta(weeks=104)), str(today)]
        x_name = "Month"
        hover = "Month: %{x|%b %Y}"

    # graph geration
    if df_commits is not None:
        fig = px.histogram(
            df_commits, x="date", range_x=x_r, labels={"x": x_name, "y": "Commits"}
        )
        fig.update_traces(
            xbins_size=interval, hovertemplate=hover + "<br>Commits: %{y}<br>"
        )
        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=interval,
            rangeslider_yaxis_rangemode="match",
        )
        fig.update_layout(
            title={
                "text": "Commits Over Time",
                "font": {"size": 28},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title=x_name,
            yaxis_title="Number of Commits",
        )
        return fig
    else:
        return None


@callback(Output("first-time-contributors", "figure"), Input("contributions", "data"))
def create_graph(data):
    df_cont = pd.DataFrame(data)

    # selection for 1st contribution only
    df_cont = df_cont[df_cont["rank"] == 1]

    # reset index to be ready for plotly
    df_cont = df_cont.reset_index()

    # Graph generation
    if df_cont is not None:
        fig = px.histogram(df_cont, x="created_at", color="Action")
        fig.update_traces(
            xbins_size="M3",
            hovertemplate="Date: %{x}" + "<br>Amount: %{y}<br><extra></extra>",
        )
        fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M3")
        fig.update_layout(
            title={
                "text": "All First time Contributors Per Quarter",
                "font": {"size": 28},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title="Quarter",
            yaxis_title="Contributions",
        )
        return fig
    else:
        return None
