from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
import numpy as np
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values

from app import jm
from pages.utils.job_utils import handle_job_state, nodata_graph
from queries.contributors_query import contributors_query as ctq
import time

gc_contributors_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Interval(
                    id="contributors-over-time-timer",
                    n_intervals=1,
                    max_intervals=1,
                    disabled=False,
                    interval=800,
                ),
                html.H4("Contributor Types Over Time", className="card-title", style={"text-align": "center"}),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on graph 3"),
                    ],
                    id="chaoss-popover-3",
                    target="chaoss-popover-target-3",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Graph(id="contributors-over-time"),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="contrib-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="contrib-time-interval",
                                        options=[
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
                                        "About Graph", id="chaoss-popover-target-3", color="secondary", size="sm"
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
                                    "Contributions Required:",
                                    html_for="num_contribs_req",
                                    width={"size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="num_contribs_req",
                                        type="number",
                                        min=1,
                                        max=15,
                                        step=1,
                                        value=4,
                                    ),
                                    className="me-2",
                                    width=2,
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


@callback(
    Output("chaoss-popover-3", "is_open"),
    [Input("chaoss-popover-target-3", "n_clicks")],
    [State("chaoss-popover-3", "is_open")],
)
def toggle_popover_3(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("contributors-over-time", "figure"),
    Output("contributors-over-time-timer", "n_intervals"),
    [
        Input("repo-choices", "data"),
        Input("contributors-over-time-timer", "n_intervals"),
        Input("num_contribs_req", "value"),
        Input("contrib-time-interval", "value"),
    ],
)
def create_graph(repolist, timer_pings, contribs, interval):
    logging.debug("COT - PONG")

    ready, results, graph_update, interval_update = handle_job_state(jm, ctq, repolist)
    if not ready:
        return graph_update, interval_update

    logging.debug("CONTRIBUTIONS_OVER_TIME_VIZ - START")
    start = time.perf_counter()

    # create dataframe from record data
    df = pd.DataFrame(results)

    # test if there is data
    if df.empty:
        logging.debug("PULL REQUESTS OVER TIME - NO DATA AVAILABLE")
        return nodata_graph, False, dash.no_update

    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df.rename(columns={"created_at": "created"}, inplace=True)

    # remove null contrib ids
    df.dropna(inplace=True)

    # create column for identifying Drive by and Repeat Contributors
    contributors = df["cntrb_id"][df["rank"] == contribs].to_list()

    # dfs for drive by and repeat contributors
    df_drive_temp = df.loc[~df["cntrb_id"].isin(contributors)]
    df_repeat_temp = df.loc[df["cntrb_id"].isin(contributors)]

    # order values chronologically by creation date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # variable to slice on to handle weekly period edge case
    period_slice = None
    if interval == "W":
        period_slice = 10

    # df for drive by contributros in time interval
    df_drive = (
        df_drive_temp.groupby(by=df_drive_temp.created.dt.to_period(interval))["cntrb_id"]
        .nunique()
        .reset_index()
        .rename(columns={"cntrb_id": "Drive", "created": "Date"})
    )
    df_drive["Date"] = pd.to_datetime(df_drive["Date"].astype(str).str[:period_slice])

    # df for repeat contributors in time interval
    df_repeat = (
        df_repeat_temp.groupby(by=df_repeat_temp.created.dt.to_period(interval))["cntrb_id"]
        .nunique()
        .reset_index()
        .rename(columns={"cntrb_id": "Repeat", "created": "Date"})
    )
    df_repeat["Date"] = pd.to_datetime(df_repeat["Date"].astype(str).str[:period_slice])

    # A single df created for plotting merged and closed as stacked bar chart
    df_drive_repeat = pd.merge(df_drive, df_repeat, on="Date", how="outer")

    # formating for graph generation
    if interval == "M":
        df_drive_repeat["Date"] = df_drive_repeat["Date"].dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_drive_repeat["Date"] = df_drive_repeat["Date"].dt.strftime("%Y-01-01")

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    fig = px.bar(
        df_drive_repeat,
        x="Date",
        y=["Repeat", "Drive"],
        labels={"x": x_name, "y": "Contributors"},
        template="minty",
    )
    fig.update_traces(
        hovertemplate=hover + "<br>Contributors: %{y}<br><extra></extra>",
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
        legend_title_text="Type",
        yaxis_title="Number of Contributors",
        margin_b=40,
    )
    logging.debug(f"CONTRIBUTIONS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
    return fig, dash.no_update
