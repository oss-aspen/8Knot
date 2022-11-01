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
                                            },  # days in milliseconds for ploty use
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

    # order values chronologically by creation date
    df = df.sort_values(by="created", axis=0, ascending=True)

    try:
        df["created"] = pd.to_datetime(df["created"], utc=True)
        df["merged"] = pd.to_datetime(df["merged"], utc=True)
        df["closed"] = pd.to_datetime(df["closed"], utc=True)
    except:
        logging.debug("PULL REQUEST STALENESS - NO DATA AVAILABLE")
        return nodata_graph, False, dash.no_update

    df_closed = df[df.merged.isnull()]
    df_merged = df

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df.iloc[0]["created"]
    latest = df.iloc[-1]["created"]

    # beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    base = [["Date", "Created", "Closed", "Merged", "Open"]]
    for date in dates:
        counts = get_merged_closed(df, date, interval)
        base.append(counts)

    df_status = pd.DataFrame(base[1:], columns=base[0])

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    if interval == "M":
        df_status["Date"] = df_status["Date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_status["Date"] = df_status["Date"].dt.year

    # graph generation
    if df_status is not None:
        fig = go.Figure()
        fig.add_bar(
            x=df_status["Date"],
            y=df_status["Created"],
            opacity=0.75,
            hovertemplate=hover + "<br>Created: %{y}<br>" + "<extra></extra>",
            offsetgroup=0,
            name="PRs Created",
        )
        fig.add_bar(
            x=df_status["Date"],
            y=df_status["Merged"],
            opacity=0.6,
            hovertemplate=hover + "<br>Merged: %{y}<br>" + "<extra></extra>",
            offsetgroup=1,
            name="PRs Merged",
        )
        fig.add_bar(
            x=df_status["Date"],
            y=df_status["Closed"],
            opacity=0.6,
            hovertemplate=[f"{hover}<br>Closed: {val}<br><extra></extra>" for val in df_status["Closed"]],
            offsetgroup=1,
            base=df_status["Merged"],
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
                x=df_status["Date"],
                y=df_status["Open"],
                mode="lines",
                name="PRs Actively Open",
                hovertemplate="PRs Open: %{y}" + "<extra></extra>",
            )
        )
        logging.debug(f"PRS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")

        # return fig, diable timer.
        return fig, dash.no_update
    else:
        # don't change figure, disable timer.
        return dash.no_update, dash.no_update


def get_merged_closed(df, date, interval):

    num_created = 0
    num_closed = 0
    num_merged = 0

    # drop rows that are more recent than the date limit
    df_lim = df[df["created"] <= date]

    df_merged = df_lim[df_lim.merged.notnull()]
    df_closed = df_lim[df_lim.closed.notnull()]

    df_open = df_lim[df_lim["closed"] > date]
    df_open = df_open.append(df_lim[df_lim.closed.isnull()])
    num_open = df_open.shape[0]

    if interval == "M":
        str_interval = date.strftime("%Y-%m")
        num_created = df_lim[df_lim["created"].dt.strftime("%Y-%m") == str_interval].shape[0]
        num_closed = df_lim[df_lim["closed"].dt.strftime("%Y-%m") == str_interval].shape[0]
        num_merged = df_lim[df_lim["merged"].dt.strftime("%Y-%m") == str_interval].shape[0]
    elif interval == "Y":
        num_created = df_lim[df_lim["created"].dt.year == date.year].shape[0]
        num_closed = df_closed[df_closed["closed"].dt.year == date.year].shape[0]
        num_merged = df_merged[df_merged["merged"].dt.year == date.year].shape[0]
    else:
        return "day"

    num_closed = num_closed - num_merged

    return [date, num_created, num_closed, num_merged, num_open]
