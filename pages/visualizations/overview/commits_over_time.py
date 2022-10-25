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
import datetime

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
                                            # TODO:
                                            # On the 'Day' setting, the graph looks terrible.
                                            # We should use "Trend" instead or find a reasonable replacement
                                            # for the resolution requested of 'Day'.
                                            # For now, removing because it isn't complete.
                                            # {
                                            #    "label": "Day",
                                            #    "value": 86400000,
                                            # },  # days in milliseconds for ploty use
                                            {"label": "Month", "value": "M1"},
                                            {"label": "Year", "value": "M12"},
                                        ],
                                        value="M1",
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

    # start timer
    start = time.perf_counter()

    # get the results from the job queue if they're available
    ready, results, graph_update, interval_update = handle_job_state(jm, cmq, repolist)
    if not ready:
        # set n_intervals to 0 so it'll fire again.
        return graph_update, interval_update

    # default time values for figure
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # process raw data into plotable format
    df = process_data(results, period)

    # create figure from processed data
    fig = create_figure(df, x_r, x_name, hover, interval)

    logging.debug(f"COMMITS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
    return fig, dash.no_update


def create_figure(df: pd.DataFrame, x_r, x_name, hover, interval):

    # create figure
    fig = px.bar(data_frame=df, x="period", y="counts", range_x=x_r, labels={"x": x_name, "y": "Commits"})

    # set figure styling
    fig.update_layout(
        xaxis_title=x_name,
        yaxis_title="Number of Commits",
        margin_b=40,
        margin_r=20,
        # fill in the height of the graph, max + 10%
        yaxis_range=[0, (df["counts"].max() * 1.10)],
    )

    # set the axes to include the rangeslider
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="instant",
        dtick=interval,
        rangeslider_yaxis_rangemode="match",
    )

    # set the hover template
    fig.update_traces(hovertemplate=hover + "<br>Commits: %{y}<br>")

    return fig


def process_data(results, period):

    # load data into dataframe
    df = pd.DataFrame(results).reset_index()

    # from POSIX timestamp to datetime
    df["date"] = pd.to_datetime(df["date"], unit="s")

    # group data by period and count instances, sort by time from earlier to later
    by_period = pd.to_datetime(df["date"]).dt.to_period(period).value_counts().sort_index()

    # because index is PeriodIndex we can convert to a series and then to a string easily
    by_period.index = pd.PeriodIndex(by_period.index).to_series().astype(str)

    # name the time index and the counts index
    by_period = by_period.rename_axis("period").reset_index(name="counts")

    return by_period
