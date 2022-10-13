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
from queries.issues_query import issues_query as iq
from app import jm

import time

gc_issues_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Interval(
                    id="issues-over-time-timer",
                    disabled=False,
                    n_intervals=1,
                    max_intervals=1,
                    interval=1500,
                ),
                html.H4(
                    "Issues Over Time",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on overview graph 3"),
                    ],
                    id="overview-popover-3",
                    target="overview-popover-target-3",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Graph(id="issues-over-time"),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="issue-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="issue-time-interval",
                                        options=[
                                            {
                                                "label": "Day",
                                                "value": 86400000,
                                            },  # days in milliseconds for ploty use
                                            {
                                                "label": "Week",
                                                "value": 604800000,
                                            },  # weeks in milliseconds for ploty use
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
                                        id="overview-popover-target-3",
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

# call backs for card graph 3 - Issue Over Time
@callback(
    Output("overview-popover-3", "is_open"),
    [Input("overview-popover-target-3", "n_clicks")],
    [State("overview-popover-3", "is_open")],
)
def toggle_popover_3(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for issues over time graph
@callback(
    Output("issues-over-time", "figure"),
    Output("issues-over-time-timer", "n_intervals"),
    [
        Input("repo-choices", "data"),
        Input("issues-over-time-timer", "n_intervals"),
        Input("issue-time-interval", "value"),
    ],
)
def issues_over_time_graph(repolist, timer_pings, interval):
    logging.debug("IOT - PONG")

    ready, results, graph_update, interval_update = handle_job_state(jm, iq, repolist)
    if not ready:
        return graph_update, interval_update

    logging.debug("ISSUES_OVER_TIME_VIZ - START")
    start = time.perf_counter()

    # create dataframe from record data
    df_issues = pd.DataFrame(results)

    # df for line chart
    df_open = make_open_df(df_issues)
    if df_open is None:
        logging.debug("ISSUES_OVER_TIME_VIZ - NO DATA AVAILABLE")
        return nodata_graph, dash.no_update

    # reset index to be ready for plotly
    df_issues = df_issues.reset_index()

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    if df_issues is not None:
        fig = go.Figure()
        fig.add_histogram(
            x=df_issues["closed"].dropna(),
            histfunc="count",
            name="closed",
            opacity=0.75,
            hovertemplate=hover + "<br>Closed: %{y}<br>" + "<extra></extra>",
        )
        fig.add_histogram(
            x=df_issues["created"],
            histfunc="count",
            name="created",
            opacity=0.6,
            hovertemplate=hover + "<br>Created: %{y}<br>" + "<extra></extra>",
        )
        fig.update_traces(xbins_size=interval)
        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=interval,
            rangeslider_yaxis_rangemode="match",
            range=x_r,
        )
        fig.update_layout(
            xaxis_title=x_name,
            yaxis_title="Number of Issues",
            bargroupgap=0.1,
            margin_b=40,
        )
        fig.add_trace(
            go.Scatter(
                x=df_open["issue"],
                y=df_open["total"],
                mode="lines",
                name="Issues Actively Open",
                hovertemplate="Issues Open: %{y}" + "<extra></extra>",
            )
        )
        logging.debug(f"ISSUES_OVER_TIME_VIZ - END - {time.perf_counter() - start}")

        # return fig, diable timer.
        return fig, dash.no_update
    else:
        # don't change figure, disable timer.
        return dash.no_update, dash.no_update


def make_open_df(df_issues):
    # created dataframe
    # TODO: dataframes don't always have the 'created_at' column for some reason.
    try:
        df_created = pd.DataFrame(df_issues["created"])
    except KeyError:
        return None

    df_created.rename(columns={"created": "issue"}, inplace=True)
    df_created["open"] = 1

    # closed dataframe
    df_closed = pd.DataFrame(df_issues["closed"]).dropna()
    df_closed.rename(columns={"closed": "issue"}, inplace=True)
    df_closed["open"] = -1

    # sum created and closed value to get actively open issues dataframe

    df_open = pd.concat([df_created, df_closed])
    df_open = df_open.sort_values("issue")
    df_open = df_open.reset_index(drop=True)
    df_open["total"] = df_open["open"].cumsum()
    df_open["issue"] = pd.to_datetime(df_open["issue"])
    df_open["issue"] = df_open["issue"].dt.floor("D")
    df_open = df_open.drop_duplicates(subset="issue", keep="last")
    df_open = df_open.drop(columns="open")
    return df_open
