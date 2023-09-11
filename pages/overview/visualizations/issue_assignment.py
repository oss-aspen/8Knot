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
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

"""


NOTE: ADDITIONAL DASH COMPONENTS FOR USER GRAPH CUSTOMIZATIONS

If you add Dash components (ie dbc.Input, dbc.RadioItems, dcc.DatePickerRange...) the ids, html_for, and targets should be in the
following format: f"component-identifier-{PAGE}-{VIZ_ID}"

NOTE: If you change or add a new query, you need to do "docker system prune -af" before building again

For more information, check out the new_vis_guidance.md
"""


# TODO: Remove unused imports and edit strings and variables in all CAPS
# TODO: Remove comments specific for the template

PAGE = "overview"  # EDIT FOR CURRENT PAGE
VIZ_ID = "issue-assignment"  # UNIQUE IDENTIFIER FOR VIZUALIZATION

gc_issue_assignment = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor Issue Assignment",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("INSERT CONTEXT OF GRAPH HERE"),
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
                                    "Total Assignments Required:",
                                    html_for=f"assignments-required-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"assignments-required-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=250,
                                        step=1,
                                        value=40,
                                        size="sm",
                                    ),
                                    className="me-2",
                                    width=1,
                                ),
                                dbc.Alert(
                                    children="No contributors meet assignment requirement",
                                    id=f"check-alert-{PAGE}-{VIZ_ID}",
                                    dismissable=True,
                                    fade=False,
                                    is_open=False,
                                    color="warning",
                                ),
                            ],
                            align="center",
                        ),
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


# callback for issue assignment graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        Input(f"assignments-required-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def issue_assignment_graph(repolist, interval, assign_req):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=iaq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=iaq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, interval, assign_req)

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, interval, assign_req):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""

    # convert to datetime objects rather than strings
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df["closed"] = pd.to_datetime(df["closed"], utc=True)
    df["assign_date"] = pd.to_datetime(df["assign_date"], utc=True)

    # order values chronologically by created date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # df of rows that are assignments
    df_contrib = df[df["assign"] == "assigned"]

    # count the assignments total for each contributor
    df_contrib = (
        df_contrib["assignee"]
        .value_counts()
        .to_frame()
        .reset_index()
        .rename(columns={"assignee": "count", "index": "assignee"})
    )

    # create list of all contributors that meet the assignment requirement
    contributors = df_contrib["assignee"][df_contrib["count"] >= assign_req].to_list()

    # no update if there are not any contributors that meet the criteria
    if len(contributors) == 0:
        return dash.no_update, True

    # only include contributors that meet the criteria
    df = df.loc[df["assignee"].isin(contributors)]

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df["created"].min()
    latest = max(df["created"].max(), df["closed"].max())

    # generating buckets beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    # df for issue assignments in date intervals
    df_assign = dates.to_frame(index=False, name="Date")

    for contrib in contributors:
        df_assign[contrib] = df_assign.apply(
            lambda row: issue_assignment(df, row.Date, contrib),
            axis=1,
        )

    # formatting for graph generation
    if interval == "M":
        df_assign["Date"] = df_assign["Date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_assign["Date"] = df_assign["Date"].dt.year

    return df_assign


def create_figure(df: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)
    contribs = df.columns.tolist()[1:]

    # making a line graph if the bin-size is small enough.
    if interval == "D":
        lines = []
        marker_val = 0
        for contrib in contribs:
            line = (
                go.Scatter(
                    name=contrib,
                    x=df["Date"],
                    y=df[contrib],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Issues Assigned: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=color_seq[marker_val]),
                ),
            )
            lines.append(line)
            marker_val = (marker_val + 1) % 6
        fig = go.Figure(lines)
    else:
        fig = px.bar(
            df,
            x="Date",
            y=contribs,
            color_discrete_sequence=color_seq,
        )

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>Issues: %{y}<br>" + "<extra></extra>")

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Issue Assignments",
        legend_title="Contriutor ID",
        font=dict(size=14),
    )

    return fig


def issue_assignment(df, date, contrib):

    # drop rows not by contrib
    df = df[df["assignee"] == contrib]

    # drop rows that are more recent than the date limit
    df_created = df[df["created"] <= date]

    # drop rows that have been closed before date
    df_in_range = df_created[df_created["closed"] > date]

    # include rows that have a null closed value
    df_in_range = pd.concat([df_in_range, df_created[df_created.closed.isnull()]])

    # get all issue unassignments
    df_unassign = df_in_range[df_in_range["assign"] == "unassigned"]

    # drop rows that have been unassigned more recent than the date limit
    df_unassign = df_unassign[df_unassign["assign_date"] <= date]

    # get all issue assignments
    df_assigned = df_in_range[df_in_range["assign"] == "assigned"]

    # drop rows that have been assigned more recent than the date limit
    df_assigned = df_assigned[df_assigned["assign_date"] <= date]

    # return the different of assignments and unassignments
    return df_assigned.shape[0] - df_unassign.shape[0]
