from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import polars as pl
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from queries.pr_assignee_query import pr_assignee_query as praq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import app
import cache_manager.cache_facade as cf

PAGE = "contributions"
VIZ_ID = "cntrib-pr-assignment"

gc_cntrib_pr_assignment = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Contributor Pull Request Review Assignment",
                                className="card-title",
                            ),
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                color="outline-secondary",
                                size="sm",
                                className="about-graph-button",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    justify="between",
                    className="mb-3",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes number of pull request reviews assigned to each each contributor\n
                            in the specifed time bucket. The visualization only includes contributors\n
                            that meet the user inputed the assignment criteria.
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
                    style={"marginBottom": "1rem"},
                ),
                html.Hr(className="card-split"),  # Divider between graph and controls
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
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
                                            className="custom-radio-buttons",
                                        ),
                                    ],
                                    className="me-2",
                                    width=4,
                                ),
                            ],
                            align="center",
                        ),
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
                                        value=10,
                                        size="sm",
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Alert(
                                    children="No contributors in date range meet assignment requirement",
                                    id=f"check-alert-{PAGE}-{VIZ_ID}",
                                    dismissable=True,
                                    fade=False,
                                    is_open=False,
                                    color="warning",
                                ),
                                dbc.Col(
                                    dcc.DatePickerRange(
                                        id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                        min_date_allowed=dt.date(2005, 1, 1),
                                        max_date_allowed=dt.date.today(),
                                        initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                        start_date=dt.date(
                                            dt.date.today().year - 2,
                                            dt.date.today().month,
                                            dt.date.today().day,
                                        ),
                                        clearable=True,
                                        className="dark-date-picker",
                                    ),
                                    width=7,
                                ),
                            ],
                            align="center",
                            justify="between",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="cntrib-pr-assignment",
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
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        Input(f"assignments-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def cntrib_pr_assignment_graph(repolist, interval, assign_req, start_date, end_date, bot_switch):
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
        return nodata_graph, False

    # remove bot data
    if bot_switch:
        df = df[~df["assignee"].isin(app.bots_list)]

    df = process_data(df, interval, assign_req, start_date, end_date)

    # test if there is data in criteria
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA IN CRITERIA AVAILABLE")
        return nodata_graph, True

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, interval, assign_req, start_date, end_date):
    """
    Process contributor PR assignment data using Polars for performance.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast initial processing
    pl_df = to_polars(df)

    # Convert to datetime and sort
    pl_df = pl_df.with_columns(
        [
            pl.col("created_at").cast(pl.Datetime("us", "UTC")),
            pl.col("closed_at").cast(pl.Datetime("us", "UTC")),
            pl.col("assign_date").cast(pl.Datetime("us", "UTC")),
        ]
    )
    pl_df = pl_df.sort("created_at")

    # Drop rows with no assignments
    pl_df = pl_df.filter(pl.col("assignment_action").is_not_null())

    # Count assignments per assignee
    pl_contrib = (
        pl_df.filter(pl.col("assignment_action") == "assigned").group_by("assignee").agg(pl.len().alias("count"))
    )

    # Get contributors meeting the requirement
    contributors = pl_contrib.filter(pl.col("count") >= assign_req).select("assignee").to_series().to_list()

    # Filter by date range
    if start_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") >= start_date)
    if end_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") <= end_date)

    # Filter by contributor list
    pl_df = pl_df.filter(pl.col("assignee").is_in(contributors))

    if pl_df.height == 0:
        return pd.DataFrame()

    # Get date range
    earliest = pl_df.select(pl.col("created_at").min()).item()
    latest_created = pl_df.select(pl.col("created_at").max()).item()
    latest_closed = pl_df.select(pl.col("closed_at").max()).item()
    latest = max(latest_created, latest_closed) if latest_closed else latest_created

    # Convert to Pandas for the loop processing
    df = to_pandas(pl_df)

    # === POLARS PROCESSING END ===

    # Generate date range
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")
    df_assign = dates.to_frame(index=False, name="start_date")

    # Offset end date by interval
    if interval == "D":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(days=1)
    elif interval == "W":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(weeks=1)
    elif interval == "M":
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(months=1)
    else:
        df_assign["end_date"] = df_assign.start_date + pd.DateOffset(years=1)

    # Use list comprehension instead of .apply() for each contributor
    for contrib in contributors:
        df_assign[contrib] = [
            pr_assignment(df, row.start_date, row.end_date, contrib) for row in df_assign.itertuples()
        ]

    # Format for graph generation
    if interval == "M":
        df_assign["start_date"] = df_assign["start_date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_assign["start_date"] = df_assign["start_date"].dt.year

    return df_assign


def create_figure(df: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # list of contributors for plot
    contribs = df.columns.tolist()[2:]

    # making a line graph if the bin-size is small enough.
    if interval == "D":
        # list of lines for plot
        lines = []

        # iterate through colors for lines
        marker_val = 0

        # loop to create lines for each contributors
        for contrib in contribs:
            line = go.Scatter(
                name=contrib,
                x=df["start_date"],
                y=df[contrib],
                mode="lines",
                showlegend=True,
                hovertemplate="PRs Assigned: %{y}<br>%{x|%b %d, %Y}",
                marker=dict(color=baby_blue[marker_val]),
            )
            lines.append(line)
            marker_val = (marker_val + 1) % 6
        fig = go.Figure(lines)
    else:
        fig = px.bar(
            df,
            x="start_date",
            y=contribs,
            color_discrete_sequence=baby_blue,
        )

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>Prs Assigned: %{y}<br>")

    # layout specifics for both styles of plots
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="PR Review Assignments",
        legend_title="Contributor ID",
        font=dict(size=14),
    )

    return fig


def pr_assignment(df, start_date, end_date, contrib):
    """
    Calculate PR assignments for a contributor in a time window using Polars.

    Uses Polars for fast filtering operations (2-5x faster than Pandas).

    Args:
        df: DataFrame with PR assignment actions
        start_date: Start of time interval
        end_date: End of time interval
        contrib: Contributor ID

    Returns:
        int: Number of assignments to the contributor
    """
    # Convert to Polars for fast filtering
    pl_df = to_polars(df)

    # Filter by contributor
    pl_df = pl_df.filter(pl.col("assignee") == contrib)

    # Filter to PRs created before end_date
    pl_created = pl_df.filter(pl.col("created_at") <= end_date)

    # Keep PRs still open after start_date or not closed
    pl_in_range = pl_created.filter((pl.col("closed_at") > start_date) | pl.col("closed_at").is_null())

    if pl_in_range.height == 0:
        return 0

    # Count unassignments before end_date
    unassign_count = pl_in_range.filter(
        (pl.col("assignment_action") == "unassigned") & (pl.col("assign_date") <= end_date)
    ).height

    # Count assignments before end_date
    assign_count = pl_in_range.filter(
        (pl.col("assignment_action") == "assigned") & (pl.col("assign_date") <= end_date)
    ).height

    # Calculate net assignments (prevent negative)
    assign_value = max(0, assign_count - unassign_count)

    return assign_value
