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
VIZ_ID = "pr_assignment"

gc_pr_assignment = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Pull Request Review Status Counts",
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
                                    className="me-2",
                                    width=4,
                                ),
                            ],
                            align="center",
                            justify="start",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="pr_assignment",
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
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def pr_assignment_graph(repolist, interval, bot_switch):
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
    """
    Process PR assignment data using Polars for performance, returning Pandas for visualization.

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

    # Use list comprehension instead of .apply()
    results = [pr_assignment(df, row.start_date, row.end_date) for row in df_assign.itertuples()]

    if results:
        df_assign["Assigned"], df_assign["Unassigned"] = zip(*results)

    # Format dates for graph generation
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
                    marker=dict(color=baby_blue[8]),
                ),
                go.Scatter(
                    name="Unassigned",
                    x=df["start_date"],
                    y=df["Unassigned"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="PRs Unassigned: %{y}<br>%{x|%b %d, %Y}<extra></extra>",
                    marker=dict(color=baby_blue[6]),
                ),
            ]
        )
    else:
        fig = px.bar(
            df,
            x="start_date",
            y=["Assigned", "Unassigned"],
            color_discrete_sequence=[baby_blue[8], baby_blue[6]],
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
    Calculate assigned and unassigned PRs in a time window using Polars.

    Uses Polars for fast filtering operations (2-5x faster than Pandas).

    Args:
        df: DataFrame with PR assignment actions
        start_date: Start of time interval
        end_date: End of time interval

    Returns:
        tuple: (num_assigned, num_unassigned)
    """
    # Convert to Polars for fast filtering
    pl_df = to_polars(df)

    # Filter to PRs created before end_date
    pl_created = pl_df.filter(pl.col("created_at") <= end_date)

    # Keep PRs still open after start_date or not closed
    pl_in_range = pl_created.filter((pl.col("closed_at") > start_date) | pl.col("closed_at").is_null())

    if pl_in_range.height == 0:
        return 0, 0

    # Count unique open PRs
    num_prs_open = pl_in_range.select(pl.col("pull_request_id").n_unique()).item()

    # Count unassignment actions before end_date
    num_unassigned_actions = pl_in_range.filter(
        (pl.col("assignment_action") == "unassigned") & (pl.col("assign_date") <= end_date)
    ).height

    # Count assignment actions before end_date
    num_assigned_actions = pl_in_range.filter(
        (pl.col("assignment_action") == "assigned") & (pl.col("assign_date") <= end_date)
    ).height

    # Calculate assigned and unassigned PRs
    num_prs_assigned = num_assigned_actions - num_unassigned_actions
    num_prs_unassigned = num_prs_open - num_prs_assigned

    return num_prs_assigned, num_prs_unassigned
