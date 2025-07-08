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
from queries.issue_assignee_query import issue_assignee_query as iaq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import app
import numpy as np
import app
import cache_manager.cache_facade as cf

PAGE = "contributions"
VIZ_ID = "issue_assignment"

gc_issue_assignment = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Issue Assignment Status Counts",
                                className="card-title",
                                style={"textAlign": "left", "fontSize": "20px", "color": "white"},
                            ),
                            width=10,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                className="text-white font-medium rounded-lg px-3 py-1.5 transition-all duration-200 cursor-pointer text-sm custom-hover-button",
                                style={
                                    "backgroundColor": "#292929",
                                    "borderColor": "#404040",
                                    "color": "white",
                                    "borderRadius": "20px",
                                    "padding": "6px 12px",
                                    "fontSize": "14px",
                                    "fontWeight": "500",
                                    "border": "1px solid #404040",
                                    "cursor": "pointer",
                                    "transition": "all 0.2s ease",
                                    "backgroundImage": "none",
                                    "boxShadow": "none",
                                },
                            ),
                            width=2,
                            className="d-flex justify-content-end",
                        ),
                    ],
                    align="center",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader(
                            "Graph Info:",
                            style={
                                "backgroundColor": "#404040",
                                "color": "white",
                                "border": "none",
                                "borderBottom": "1px solid #606060",
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "padding": "12px 16px",
                            },
                        ),
                        dbc.PopoverBody(
                            """
                            Visualizes the number of assigned and unassigned issues in each \n
                            time bucket.
                            """,
                            style={
                                "backgroundColor": "#292929",
                                "color": "#E0E0E0",
                                "border": "none",
                                "fontSize": "14px",
                                "lineHeight": "1.5",
                                "padding": "16px",
                            },
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                    style={
                        "backgroundColor": "#292929",
                        "border": "1px solid #606060",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.3)",
                        "maxWidth": "400px",
                    },
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                html.Hr(
                    style={
                        "borderColor": "#e0e0e0",
                        "margin": "1.5rem -2rem",
                        "width": "calc(100% + 4rem)",
                        "marginLeft": "-2rem",
                    }
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Date Interval:",
                                            html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                            style={"marginBottom": "8px", "fontSize": "14px"},
                                        ),
                                        dbc.RadioItems(
                                            id=f"date-radio-{PAGE}-{VIZ_ID}",
                                            className="modern-radio-buttons-small",
                                            options=[
                                                {"label": "Trend", "value": "D"},
                                                {"label": "Week", "value": "W"},
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="W",
                                            inline=True,
                                        ),
                                    ],
                                    width="auto",
                                ),
                            ],
                            justify="start",
                        ),
                    ]
                ),
            ]
        )
    ],
    style={"padding": "20px", "borderRadius": "10px", "backgroundColor": "#292929", "border": "1px solid #404040"},
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


# callback for issue assignment graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def cntrib_issue_assignment_graph(repolist, interval, bot_switch):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=iaq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID} - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # data ready.
    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=iaq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # remove assignment data if assigned to a bot
    if bot_switch:
        df["bot"] = df["assignee"].isin(app.bots_list)
        df.loc[df.bot == True, "assign_date"] = None
        df.loc[df.bot == True, "assignment_action"] = None
        df.loc[df.bot == True, "assignee"] = None

    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df["closed_at"] = pd.to_datetime(df["closed_at"], utc=True)
    df["assign_date"] = pd.to_datetime(df["assign_date"], utc=True)

    # order values chronologically by created date
    df = df.sort_values(by="created_at", axis=0, ascending=True)

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df["created_at"].min()
    latest = max(df["created_at"].max(), df["closed_at"].max())

    # generating buckets beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    # df for issue assignments in date intervals
    df_assign = dates.to_frame(index=False, name="start_date")

    # offset end date column by interval
    if interval == "D":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(days=1)
    elif interval == "W":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(weeks=1)
    elif interval == "M":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(months=1)
    else:
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(years=1)

    # dynamically apply the function to all dates defined in the date_range to create df_status
    df_assign["Assigned"], df_assign["Unassigned"] = zip(
        *df_assign.apply(
            lambda row: issue_assignment(df, row.start_date, row.end_date),
            axis=1,
        )
    )

    # formatting for graph generation
    if interval == "M":
        df_assign["start_date"] = df_assign["start_date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_assign["start_date"] = df_assign["start_date"].dt.year

    return df_assign


def create_figure(df: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # making a line graph if the bin-size is small enough.
    if interval == "D":
        fig = go.Figure(
            [
                go.Scatter(
                    name="Assigned",
                    x=df["start_date"],
                    y=df["Assigned"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Issues Assigned: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=color_seq[2]),
                ),
                go.Scatter(
                    name="Unassigned",
                    x=df["start_date"],
                    y=df["Unassigned"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Issues Unassigned: %{y}<br>%{x|%b %d, %Y}<extra></extra>",
                    marker=dict(color=color_seq[3]),
                ),
            ]
        )
    else:
        fig = px.bar(
            df,
            x="start_date",
            y=["Assigned", "Unassigned"],
            color_discrete_sequence=[color_seq[2], color_seq[3]],
        )

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>Issues: %{y}<br><extra></extra>")

        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=period,
            rangeslider_yaxis_rangemode="match",
            range=x_r,
        )

    # layout specifics for both styles of plots
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Issues",
        legend_title="Types",
        font=dict(size=14),
        plot_bgcolor="#292929",
        paper_bgcolor="#292929",
    )

    return fig


def issue_assignment(df, start_date, end_date):
    """
    This function takes a start and a end date and determines how many
    issues in that time interval are assigned and unassigned.

    Args:
    -----
        df : Pandas Dataframe
            Dataframe with issue assignment actions of the assignees

        start_date : Datetime Timestamp
            Timestamp of the start time of the time interval

        end_date : Datetime Timestamp
            Timestamp of the end time of the time interval

    Returns:
    --------
        int, int: Number of assigned and unassigned issues in the time window
    """

    # drop rows that are more recent than the end date
    df_created = df[df["created_at"] <= end_date]

    # Keep issues that were either still open after the 'start_date' or that have not been closed.
    df_in_range = df_created[(df_created["closed_at"] > start_date) | (df_created["closed_at"].isnull())]

    # number of issues open in time interval
    num_issues_open = df_in_range["issue_id"].nunique()

    # get all issue unassignments and drop rows that have been unassigned more recent than the end date
    num_unassigned_actions = df_in_range[
        (df_in_range["assignment_action"] == "unassigned") & (df_in_range["assign_date"] <= end_date)
    ].shape[0]

    # get all issue assignments and drop rows that have been assigned more recent than the end date
    num_assigned_actions = df_in_range[
        (df_in_range["assignment_action"] == "assigned") & (df_in_range["assign_date"] <= end_date)
    ].shape[0]

    # number of assigned issues during the time interval
    num_issues_assigned = num_assigned_actions - num_unassigned_actions

    # number of unassigned issues during the time interval
    num_issues_unassigned = num_issues_open - num_issues_assigned

    # return the number of assigned and unassigned issues
    return num_issues_assigned, num_issues_unassigned
