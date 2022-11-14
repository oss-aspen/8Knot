from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values

from pages.utils.job_utils import handle_job_state, nodata_graph
from queries.commits_query import commits_query as cmq
from app import jm
import time

gc_commits_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Interval(
                    id="commits-over-time-timer",
                    disabled=False,
                    n_intervals=1,
                    max_intervals=1,
                    interval=1500,
                ),
                html.H4(
                    "Commits Over Time",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on overview graph 2"),
                    ],
                    id="overview-popover-2",
                    target="overview-popover-target-2",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Graph(id="commits-over-time"),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="commits-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="commits-time-interval",
                                        options=[
                                            {
                                                "label": "Day",
                                                "value": "D",
                                            },
                                            {
                                                "label": "Week",
                                                "value": "W",
                                            },
                                            {"label": "Month", "value": "M"},
                                            {"label": "Year", "value": "Y"},
                                        ],
                                        value="M",
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-2",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
    color="light",
)

# call backs for card graph 2 - Commits Over Time
@callback(
    Output("overview-popover-2", "is_open"),
    [Input("overview-popover-target-2", "n_clicks")],
    [State("overview-popover-2", "is_open")],
)
def toggle_popover_2(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for commits over time graph
@callback(
    Output("commits-over-time", "figure"),
    Output("commits-over-time-timer", "n_intervals"),
    [
        Input("repo-choices", "data"),
        Input("commits-over-time-timer", "n_intervals"),
        Input("commits-time-interval", "value"),
    ],
)
def create_commits_over_time_graph(repolist, timer_pings, interval):
    logging.debug("COT - PONG")

    ready, results, graph_update, interval_update = handle_job_state(jm, cmq, repolist)
    if not ready:
        # set n_intervals to 0 so it'll fire again.
        return graph_update, interval_update

    logging.debug("COMMITS_OVER_TIME_VIZ - START")
    start = time.perf_counter()

    # create dataframe from record data
    df = pd.DataFrame(results)

    # test if there is data
    if df.empty:
        logging.debug("COMMITS OVER TIME - NO DATA AVAILABLE")
        return nodata_graph, False, dash.no_update

    # convert to datetime objects with consistent column name
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df.rename(columns={"date": "created"}, inplace=True)

    # variable to slice on to handle weekly period edge case
    period_slice = None
    if interval == "W":
        # this is to slice the extra period information that comes with the weekly case
        period_slice = 10

    # get the count of commits in the desired interval in pandas period format, sort index to order entries
    df_created = (
        df.groupby(by=df.created.dt.to_period(interval))["commits"]
        .nunique()
        .reset_index()
        .rename(columns={"created": "Date"})
    )

    # converts date column to a datetime object, converts to string first to handle period information
    # the period slice is to handle weekly corner case
    df_created["Date"] = pd.to_datetime(df_created["Date"].astype(str).str[:period_slice])

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph geration
    fig = px.bar(df_created, x="Date", y="commits", range_x=x_r, labels={"x": x_name, "y": "Commits"})
    fig.update_traces(hovertemplate=hover + "<br>Commits: %{y}<br>")
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        rangeslider_yaxis_rangemode="match",
        range=x_r,
    )
    fig.update_layout(
        xaxis_title=x_name,
        yaxis_title="Number of Commits",
        margin_b=40,
        margin_r=20,
    )
    logging.debug(f"COMMITS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
    return fig, dash.no_update
