from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.release_query import release_query as relq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import math
import numpy as np


PAGE = "starterHealth"
VIZ_ID = "release_freq"

gc_release_freq = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "release_freq",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """This visualization gives a view into the development lifecycle of a repository\n
                             releases are a key view into what a project is doing and how lively it is. """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.DatePickerRange(
                                        id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                        min_date_allowed=dt.date(2005, 1, 1),
                                        max_date_allowed=dt.date.today(),
                                        initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                        clearable=True,
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                            justify="between",
                        ),
                    ]
                ),
            ]
        )
    ],
)


# callback for graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for Project Velocity graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)
def project_velocity_graph(
    repolist, start_date, end_date
):

    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=relq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=relq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df = process_data(df, start_date, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(
    df: pd.DataFrame,
    start_date,
    end_date
):

    # convert to datetime objects rather than strings
    df["release_published_at"] = pd.to_datetime(df["release_published_at"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="release_published_at", axis=0, ascending=True)
    df = df.insert(0, "y_axis", [1])

    # filter values based on date picker
    if start_date is not None:
        df = df[df.release_published_at >= start_date]
    if end_date is not None:
        df = df[df.release_published_at <= end_date]

    return df


def create_figure(df: pd.DataFrame):

    y_axis = "release_id" # should be y axis col
    y_title = "Releases"

    # graph generation
    fig = px.scatter(
        df,
        x="created",
        y=y_axis,
        color="repo_name",
        color_discrete_sequence=color_seq,
    )

    # layout styling
    fig.update_layout(
        xaxis_title="Release Date",
        yaxis_title=y_title,
        margin_b=40,
        font=dict(size=14),
        legend_title="Repo Name",
    )

    return fig
