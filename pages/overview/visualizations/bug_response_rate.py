from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.issues_bugs_query import issues_bugs_query as ibq
from pages.utils.job_utils import nodata_graph
from cache_manager.cache_manager import CacheManager as cm
import io
import time

gc_bug_response_rate = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Bug Response Rate",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            'This visualization shows how long it takes to close each issue which is labeled as either a "bug" or "defect".\n\
                            It also gives the average time taken to close all issues labeled "bug" or "defect".'
                        ),
                    ],
                    id="overview-popover-br",
                    target="overview-popover-target-br",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id="bug_response_rate"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Mean Bug Response Rate:",
                                    html_for="bug-response-avg",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Badge(
                                            f"NaN",
                                            id="bug-response-avg",
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-br",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Time Interval:",
                                    html_for="bug-response-interval",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id="bug-response-interval",
                                            options=[
                                                {"label": "Seconds", "value": 1},
                                                {"label": "Minutes", "value": 60},
                                                {"label": "Hours", "value": 60 * 60},
                                                {"label": "Days", "value": 60 * 60 * 24},
                                                {"label": "Weeks", "value": 60 * 60 * 24 * 7},
                                                {"label": "Months", "value": 60 * 60 * 24 * 30},
                                                {"label": "Years", "value": 60 * 60 * 24 * 365},
                                            ],
                                            value=1,
                                            inline=True,
                                        ),
                                    ]
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        )
    ],
    # color="light",
)


@callback(
    Output("overview-popover-br", "is_open"),
    [Input("overview-popover-target-br", "n_clicks")],
    [State("overview-popover-br", "is_open")],
)
def toggle_popover_bugs(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("bug_response_rate", "figure"),
    Output("bug-response-avg", "children"),
    [
        Input("repo-choices", "data"),
        Input("bug-response-interval", "value"),
    ],
    background=True,
)
def new_bug_response_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ibq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ibq, repos=repolist)

    # data ready
    start = time.perf_counter()
    logging.debug("ISSUES BUGS RESPONSE - START")

    # test if there is data
    if df.empty:
        logging.debug("ISSUES BUGS - NO DATA AVAILABLE")
        return nodata_graph, False
    start = time.perf_counter()

    # function for all data pre processing
    df_status = process_data(df, interval)

    fig = create_figure(df_status, interval)
    mean_response_rate = df_status["age"].mean()

    logging.debug(f"BUG RESPONSE - END - {time.perf_counter() - start}")
    return fig, mean_response_rate


def process_data(df: pd.DataFrame, interval):
    # filter the data for the "bug" and "defect" labels.
    df_status = filter_for_labels(df)

    # apply issue_ids to string to render only the issues present.
    df_status["issue_id"] = df_status["issue_id"].apply(str)

    # normalize the age according to the interval input by the user.
    df_status["age"] = df_status["age"].div(interval)

    return df_status


def create_figure(df_status: pd.DataFrame, interval):
    # Bar Graph
    # fig = px.bar(df_status, x="issue_id", y="age", color_discrete_sequence=[color_seq[3]])
    # fig.update_layout(xaxis_title="Issue ID", yaxis_title="Response Time", legend_title="Type")

    # Empirical Cumulative Distribution Function (ECDF) [Survival Analysis]
    fig = px.ecdf(df_status, x="age")
    fig.update_layout(xaxis_title="Age", yaxis_title="Probability of Still Being Open")
    return fig


def filter_for_labels(df: pd.DataFrame):
    # send all labels to lowercase for consistency
    df["label_text"] = df["label_text"].str.lower()

    # get issues labeled "bug"
    bug = df.loc[df["label_text"].str.contains("bug")]

    # Get issues labeled "defect"
    defect = df.loc[df["label_text"].str.contains("defect")]

    # Drop duplicates (if there's labels containing both)
    df = pd.concat([bug, defect]).drop_duplicates()

    # Drop duplicate entries of the same issue
    return df.drop_duplicates(subset=["issue_id"])
