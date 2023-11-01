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
from queries.pr_assignee_query import pr_assignee_query as praq
from pages.utils.job_utils import nodata_graph
import time
import cache_manager.cache_facade as cf

PAGE = "contributions"
VIZ_ID = "pr_assignment"

gc_pr_assignment = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Pull Request Review Status Counts",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes the number of assigned and unassigned pull requests in each \n
                            time bucket.
                            """
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
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-radio-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "Trend", "value": "D"},
                                                {"label": "Week", "value": "W"},
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="W",
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


# callback for pull request review assignment graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [Input("repo-choices", "data"), Input(f"date-radio-{PAGE}-{VIZ_ID}", "value")],
    background=True,
)
def pr_assignment_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=praq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID} - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # data ready.
    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=praq.__name__,
        repolist=repolist,
    )

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    # convert to datetime objects rather than strings
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df["closed"] = pd.to_datetime(df["closed"], utc=True)
    df["assign_date"] = pd.to_datetime(df["assign_date"], utc=True)

    # order values chronologically by created date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df["created"].min()
    latest = max(df["created"].max(), df["closed"].max())

    # generating buckets beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    # df for pr review assignments in date intervals
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
            lambda row: pr_assignment(df, row.start_date, row.end_date),
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
                    hovertemplate="PRs Assigned: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=color_seq[2]),
                ),
                go.Scatter(
                    name="Unassigned",
                    x=df["start_date"],
                    y=df["Unassigned"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="PRs Unassigned: %{y}<br>%{x|%b %d, %Y}<extra></extra>",
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
        fig.update_traces(hovertemplate=hover + "<br>PRs: %{y}<br><extra></extra>")

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
        yaxis_title="Pull Requests",
        legend_title="Types",
        font=dict(size=14),
    )

    return fig


def pr_assignment(df, start_date, end_date):
    """
    This function takes a start and a end date and determines how many
    prs in that time interval are assigned and unassigned.

    Args:
    -----
        df : Pandas Dataframe
            Dataframe with pr assignment actions of the assignees

        start_date : Datetime Timestamp
            Timestamp of the start time of the time interval

        end_date : Datetime Timestamp
            Timestamp of the end time of the time interval

    Returns:
    --------
        int, int: Number of assigned and unassigned prs in the time window
    """

    # drop rows that are more recent than the end date
    df_created = df[df["created"] <= end_date]

    # Keep prs that were either still open after the 'start_date' or that have not been closed.
    df_in_range = df_created[(df_created["closed"] > start_date) | (df_created["closed"].isnull())]

    # number of prs open in time interval
    num_prs_open = df_in_range["pull_request_id"].nunique()

    # get all pr review unassignments and drop rows that have been unassigned more recent than the end date
    num_unassigned_actions = df_in_range[
        (df_in_range["assignment_action"] == "unassigned") & (df_in_range["assign_date"] <= end_date)
    ].shape[0]

    # get all issue assignments and drop rows that have been assigned more recent than the end date
    num_assigned_actions = df_in_range[
        (df_in_range["assignment_action"] == "assigned") & (df_in_range["assign_date"] <= end_date)
    ].shape[0]

    # number of assigned prs during the time interval
    num_prs_assigned = num_assigned_actions - num_unassigned_actions

    # number of unassigned prs during the time interval
    num_prs_unassigned = num_prs_open - num_prs_assigned

    # return the number of assigned and unassigned prs
    return num_prs_assigned, num_prs_unassigned
