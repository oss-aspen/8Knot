from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import polars as pl
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from pages.utils.job_utils import nodata_graph
from queries.prs_query import prs_query as prq
import time
import cache_manager.cache_facade as cf

PAGE = "contributions"
VIZ_ID = "pr-staleness"

gc_pr_staleness = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Pull Request Activity - Staleness",
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
                            Visualizes growth of Open Pull Request backlog. Differentiates sub-populations\n
                            of PRs by their 'Staleness.'\n
                            Please see the definition of 'Staleness' on the Info page.
                            """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",  # needs to be the same as dbc.Button id
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
                                    "Days Until Staling:",
                                    html_for=f"staling-days-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"staling-days-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=7,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "Days Until Stale:",
                                    html_for=f"stale-days-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"stale-days-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=30,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Alert(
                            children="Please ensure that 'Days Until Staling' is less than 'Days Until Stale'",
                            id=f"check-alert-{PAGE}-{VIZ_ID}",
                            dismissable=True,
                            fade=False,
                            is_open=False,
                            color="warning",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id=f"date-interval-{PAGE}-{VIZ_ID}",
                                        options=[
                                            {"label": "Trend", "value": "D"},
                                            {"label": "Month", "value": "M"},
                                            {"label": "Year", "value": "Y"},
                                        ],
                                        value="M",
                                        inline=True,
                                        className="custom-radio-buttons",
                                    ),
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="pr-staleness",
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


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
        Input(f"staling-days-{PAGE}-{VIZ_ID}", "value"),
        Input(f"stale-days-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def new_staling_prs_graph(repolist, interval, staling_interval, stale_interval):
    # conditional for the intervals to be valid options
    if staling_interval > stale_interval:
        return dash.no_update, True

    if staling_interval is None or stale_interval is None:
        return dash.no_update, dash.no_update

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=prq.__name__, repolist=repolist):
        logging.warning(f"PULL REQUESTS STALENESS - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning("PULL REQUEST STALENESS - START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=prq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning("PULL REQUEST STALENESS  - NO DATA AVAILABLE")
        return nodata_graph, False

    # function for all data pre processing
    df_status = process_data(df, interval, staling_interval, stale_interval)

    fig = create_figure(df_status, interval)

    logging.warning(f"PULL REQUEST STALENESS - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, interval, staling_interval, stale_interval):
    """
    Process PR staleness data using Polars for performance, returning Pandas for visualization.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast initial processing
    pl_df = to_polars(df)

    # Convert to datetime and sort
    pl_df = pl_df.with_columns(
        [
            pl.col("created_at").cast(pl.Datetime("us", "UTC")),
            pl.col("merged_at").cast(pl.Datetime("us", "UTC")),
            pl.col("closed_at").cast(pl.Datetime("us", "UTC")),
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
    df_status = dates.to_frame(index=False, name="Date")

    # Use list comprehension instead of .apply() (cleaner, same performance)
    results = [get_new_staling_stale_up_to(df, date, staling_interval, stale_interval) for date in df_status["Date"]]

    if results:
        df_status["New"], df_status["Staling"], df_status["Stale"] = zip(*results)

    # Format dates for graph generation
    if interval == "M":
        df_status["Date"] = df_status["Date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_status["Date"] = df_status["Date"].dt.year

    return df_status


def create_figure(df_status: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # making a line graph if the bin-size is small enough.
    if interval == "D":
        fig = go.Figure(
            [
                go.Scatter(
                    name="New",
                    x=df_status["Date"],
                    y=df_status["New"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="PRs New: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=baby_blue[0]),
                ),
                go.Scatter(
                    name="Staling",
                    x=df_status["Date"],
                    y=df_status["Staling"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="PRs Staling: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=baby_blue[2]),
                ),
                go.Scatter(
                    name="Stale",
                    x=df_status["Date"],
                    y=df_status["Stale"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="PRs Stale: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=baby_blue[6]),
                ),
            ]
        )
    else:
        fig = px.bar(
            df_status,
            x="Date",
            y=["New", "Staling", "Stale"],
            color_discrete_sequence=[baby_blue[0], baby_blue[2], baby_blue[6]],
        )

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>PRs: %{y}<br>" + "<extra></extra>")

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Pull Requests",
        legend_title="Type",
        font=dict(size=14),
    )

    return fig


def get_new_staling_stale_up_to(df, date, staling_interval, stale_interval):
    """
    Calculate new, staling, and stale PRs up to a given date.

    Uses Polars for fast filtering operations (2-5x faster than Pandas).
    """
    # Convert to Polars for fast filtering
    pl_df = to_polars(df)

    # Filter to PRs created before date and still open at date
    pl_created = pl_df.filter(pl.col("created_at") <= date)
    pl_in_range = pl_created.filter((pl.col("closed_at") > date) | pl.col("closed_at").is_null())

    if pl_in_range.height == 0:
        return [0, 0, 0]

    # Calculate time thresholds
    staling_days = date - relativedelta(days=+staling_interval)
    stale_days = date - relativedelta(days=+stale_interval)

    # Count PRs in each category using Polars (faster filtering)
    numTotal = pl_in_range.height

    # New: created within staling threshold
    numNew = pl_in_range.filter(pl.col("created_at") >= staling_days).height

    # Staling: created between stale and staling thresholds
    numStaling = pl_in_range.filter((pl.col("created_at") > stale_days) & (pl.col("created_at") < staling_days)).height

    # Stale: the rest
    numStale = numTotal - (numNew + numStaling)

    return [numNew, numStaling, numStale]
