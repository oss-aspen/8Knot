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
from queries.release_query import release_frequency_query as refq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import math
import numpy as np


PAGE = "Sprint 1"
VIZ_ID = "release-frequency"

gc_release_frequency = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Release Frequency",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """This visualization gives a view into the development speed of a repository in\n
                            relation to the other selected repositories. For more context of this visualization see\n
                            https://chaoss.community/kb/metric-project-velocity/ \n
                            https://www.cncf.io/blog/2017/06/05/30-highest-velocity-open-source-projects/ """
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
    df = cache.grabm(func=refq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=refq, repos=repolist)

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


    # order values chronologically by date
    df = df.sort_values(by="release_published_at", axis=0, ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.release_published_at >= start_date]
    if end_date is not None:
        df = df[df.release_published_at <= end_date]

    df["release_intervals"] = [float(0) for x in range(len(df["release_published_at"]))]

    for i in range(len(df["release_published_at"]) - 1):
        temp = df.iloc[i + 1]["release_published_at"] - df.iloc[i]["release_published_at"]
        df.iloc[i + 1, 3] = float(temp.total_seconds() / 86400)
    df.iloc[0, 3] = float(0)
    df = df[df.release_intervals >= 1.0]

    # pivot df to reformat the actions to be columns and repo_id to be rows
    # df_actions = df_actions.pivot(index="repo_name", columns="Action", values="count")

    return df


def create_figure(df: pd.DataFrame):

    # graph generation
    fig = px.histogram(
        df,
        x="release_intervals",
        #color="repo_name",
        #size="log_num_contrib",
        hover_data=["release_intervals"],
        #color_discrete_sequence=color_seq,
    )

    # fig.update_traces(
    #     hovertemplate="Interval length: %{customdata[0]}"
    # )

    # layout styling
    fig.update_layout(
        xaxis_title="Release Intervals (Days)",
        yaxis_title="Count",
        margin_b=40,
        font=dict(size=14),
    )

    return fig
