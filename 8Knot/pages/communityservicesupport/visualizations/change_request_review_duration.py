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
from queries.prs_query import prs_query as prs
from queries.pr_response_query import pr_response_query as prr
from queries.pr_assignee_query import pr_assignee_query as pra
from queries.change_request_review_query import change_request_review_query as crr
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import math
import numpy as np


PAGE = "Community Service and Support"
VIZ_ID = "change-request-review-duration"

gc_change_request_review_duration = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Change Request Review Duration",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """This visualization provides insights into the review process of change requests in a project. \n 
                            It highlights aspects such as the extent of formal reviews, the number of reviews, the nature of comments, \n
                            and the acceptance or decline of change requests. For more context of this visualization see \n
                            https://chaoss.community/kb/metric-change-request-reviews/ \n """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",  # needs to be the same as dbc.Button id
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
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-interval-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "Trend", "value": "D"},
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
                                            inline=True,
                                        ),
                                    ]
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

# callback for Change Request Review Duration graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    # Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"), USE WITH ADDITIONAL PARAMETERS
    # if additional output is added, change returns accordingly
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        # add additional inputs here
    ],
    background=True,
)
def change_request_review_duration_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=prs, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=prs, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    # convert to datetime objects rather than strings
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df["merged"] = pd.to_datetime(df["merged"], utc=True)
    df["closed"] = pd.to_datetime(df["closed"], utc=True)
    
    # ensure pull request unique ID are formatted
    #df["pull_request"] = df["pull_request"].astype(str)
    #df["pull_request"] = df["pull_request"].str[:15]

    # order values chronologically by creation date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df["created"].min()
    latest = max(df["created"].max(), df["closed"].max())

    # generating buckets beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    # df for new, staling, and stale prs for time interval
    df_status = dates.to_frame(index=False, name="Date")

    # formatting for graph generation
    if interval == "M":
        df_status["Date"] = df_status["Date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_status["Date"] = df_status["Date"].dt.year

    return df_status

#TODO: Update the figure pieces
def create_figure(df_status: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    fig = px.bar(
        df_status,
        x="Date",
        y=["Rejected-Bot", "Rejected-Human", "Approved-Bot", "Approved-Human"],
        color_discrete_sequence=[color_seq[1], color_seq[5], color_seq[2], color_seq[0]],
    )

    # edit hover values
    fig.update_traces(hovertemplate=hover + "<br>PRs: %{y}<br>" + "<extra></extra>")

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Review Duration",
        legend_title="Type",
        font=dict(size=14),
    )

    return fig
