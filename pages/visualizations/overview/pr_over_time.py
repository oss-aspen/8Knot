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
from queries.prs_query import prs_query as prq
from app import jm

import time

gc_pr_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Interval(
                    id="prs-over-time-timer",
                    disabled=False,
                    n_intervals=1,
                    max_intervals=1,
                    interval=1500,
                ),
                html.H4(
                    "Pull Requests Over Time",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on overview graph 7"),
                    ],
                    id="overview-popover-7",
                    target="overview-popover-target-7",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Graph(id="prs-over-time"),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="pr-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="pr-time-interval",
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
                                        id="overview-popover-target-7",
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

# call backs for card graph 7 - Pull Request Over Time
@callback(
    Output("overview-popover-7", "is_open"),
    [Input("overview-popover-target-7", "n_clicks")],
    [State("overview-popover-7", "is_open")],
)
def toggle_popover_7(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for prs over time graph
@callback(
    Output("prs-over-time", "figure"),
    Output("prs-over-time-timer", "n_intervals"),
    [
        Input("repo-choices", "data"),
        Input("prs-over-time-timer", "n_intervals"),
        Input("pr-time-interval", "value"),
    ],
)
def prs_over_time_graph(repolist, timer_pings, interval):
    logging.debug("IOT - PONG")

    ready, results, graph_update, interval_update = handle_job_state(jm, prq, repolist)
    if not ready:
        return graph_update, interval_update

    logging.debug("PRS_OVER_TIME_VIZ - START")
    start = time.perf_counter()

    # create dataframe from record data
    df = pd.DataFrame(results)

    # test if there is data
    if df.empty:
        logging.debug("PULL REQUESTS OVER TIME - NO DATA AVAILABLE")
        return nodata_graph, False, dash.no_update

    # convert dates to datetime objects rather than strings
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df["merged"] = pd.to_datetime(df["merged"], utc=True)
    df["closed"] = pd.to_datetime(df["closed"], utc=True)

    # order values chronologically by creation date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # variable to slice on to handle weekly period edge case
    period_slice = None
    if interval == "W":
        period_slice = 10

    # data frames for PR created, merged, or closed. Detailed description applies for all 3.

    # get the count of created prs in the desired interval in pandas period format, sort index to order entries
    created_range = df["created"].dt.to_period(interval).value_counts().sort_index()

    # converts to data frame object and created date column from period values
    df_created = created_range.to_frame().reset_index().rename(columns={"index": "Date"})

    # converts date column to a datetime object, converts to string first to handle period information
    # the period slice is to handle weekly corner case
    df_created["Date"] = pd.to_datetime(df_created["Date"].astype(str).str[:period_slice])

    # df for merged prs in time interval
    merged_range = pd.to_datetime(df["merged"]).dt.to_period(interval).value_counts().sort_index()
    df_merged = merged_range.to_frame().reset_index().rename(columns={"index": "Date"})
    df_merged["Date"] = pd.to_datetime(df_merged["Date"].astype(str).str[:period_slice])

    # df for closed prs in time interval
    closed_range = pd.to_datetime(df["closed"]).dt.to_period(interval).value_counts().sort_index()
    df_closed = closed_range.to_frame().reset_index().rename(columns={"index": "Date"})
    df_closed["Date"] = pd.to_datetime(df_closed["Date"].astype(str).str[:period_slice])

    # A single df created for plotting merged and closed as stacked bar chart
    df_closed_merged = pd.merge(df_merged, df_closed, on="Date", how="outer")

    if interval == "M":
        df_created["Date"] = df_created["Date"].dt.strftime("%Y-%m-01")
        df_closed_merged["Date"] = df_closed_merged["Date"].dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_created["Date"] = df_created["Date"].dt.strftime("%Y-01-01")
        df_closed_merged["Date"] = df_closed_merged["Date"].dt.strftime("%Y-01-01")

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df.iloc[0]["created"]
    latest = df.iloc[-1]["created"]

    # beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq="D", inclusive="both")

    # df for open prs from time interval
    df_open = dates.to_frame(index=False, name="Date")

    # aplies function to get the amount of open prs for each day
    df_open["Open"] = df_open.apply(lambda row: get_open(df, row.Date), axis=1)

    df_open["Date"] = df_open["Date"].dt.strftime("%Y-%m-%d")

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    fig = go.Figure()
    fig.add_bar(
        x=df_created["Date"],
        y=df_created["created"],
        opacity=0.75,
        hovertemplate=hover + "<br>Created: %{y}<br>" + "<extra></extra>",
        offsetgroup=0,
        name="PRs Created",
    )
    fig.add_bar(
        x=df_closed_merged["Date"],
        y=df_closed_merged["merged"],
        opacity=0.6,
        hovertemplate=hover + "<br>Merged: %{y}<br>" + "<extra></extra>",
        offsetgroup=1,
        name="PRs Merged",
    )
    fig.add_bar(
        x=df_closed_merged["Date"],
        y=df_closed_merged["closed"],
        opacity=0.6,
        hovertemplate=[f"{hover}<br>Closed: {val}<br><extra></extra>" for val in df_closed_merged["closed"]],
        offsetgroup=1,
        base=df_closed_merged["merged"],
        name="PRs Closed",
    )
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        rangeslider_yaxis_rangemode="match",
        range=x_r,
    )
    fig.update_layout(
        xaxis_title=x_name,
        yaxis_title="Number of PRs",
        bargroupgap=0.1,
        margin_b=40,
    )
    fig.add_trace(
        go.Scatter(
            x=df_open["Date"],
            y=df_open["Open"],
            mode="lines",
            name="PRs Actively Open",
            hovertemplate="PRs Open: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
        )
    )
    logging.debug(f"PRS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")

    # return fig, diable timer.
    return fig, dash.no_update


# for each day, this function calculates the amount of open prs
def get_open(df, date):

    # drop rows that are more recent than the date limit
    df_created = df[df["created"] <= date]

    # drops rows that have been closed after date
    df_open = df_created[df_created["closed"] > date]

    # include prs that have not been close yet
    df_open = pd.concat([df_open, df_created[df_created.closed.isnull()]])

    # generates number of columns ie open prs
    num_open = df_open.shape[0]
    return num_open
