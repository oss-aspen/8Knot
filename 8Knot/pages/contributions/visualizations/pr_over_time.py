from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import polars as pl
import numpy as np
import logging
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from pages.utils.job_utils import nodata_graph
from queries.prs_query import prs_query as prq
import time
import cache_manager.cache_facade as cf

PAGE = "contributions"
VIZ_ID = "prs-over-time"

gc_pr_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Pull Requests Over Time",
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
                            Visualizes PR behavior by tracking Created, Merged, and Closed-Not-Merged PRs over time.\n
                            Also shows Created PR count as a trend over lifespan.
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
                                    html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id=f"date-interval-{PAGE}-{VIZ_ID}",
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
                                        className="custom-radio-buttons",
                                    ),
                                    className="me-2",
                                    width=4,
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        ),
    ],
    className="dark-card",
    id="prs-over-time",
)


# formatting for graph generation
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for prs over time graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def prs_over_time_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=prq.__name__, repolist=repolist):
        logging.warning(f"PULL REQUESTS OVER TIME - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # data ready.
    start = time.perf_counter()
    logging.warning("PULL REQUESTS OVER TIME - START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=prq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning("PULL REQUESTS OVER TIME - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df_created, df_closed_merged, df_open = process_data(df, interval)

    fig = create_figure(df_created, df_closed_merged, df_open, interval)

    logging.warning(f"PRS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")

    return fig


def process_data(df: pd.DataFrame, interval):
    """
    Process PR data using Polars for performance, returning Pandas for visualization.

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

    # Convert back to Pandas for period operations (Polars doesn't have period support)
    df = to_pandas(pl_df)

    # === POLARS PROCESSING END ===

    # variable to slice on to handle weekly period edge case
    period_slice = None
    if interval == "W":
        period_slice = 10

    # Data frames for PR created, merged, or closed
    created_range = df["created_at"].dt.to_period(interval).value_counts().sort_index()
    df_created = created_range.to_frame().reset_index().rename(columns={"created_at": "Date", "count": "created_at"})
    df_created["Date"] = pd.to_datetime(df_created["Date"].astype(str).str[:period_slice])

    merged_range = pd.to_datetime(df["merged_at"]).dt.to_period(interval).value_counts().sort_index()
    df_merged = merged_range.to_frame().reset_index().rename(columns={"merged_at": "Date", "count": "merged_at"})
    df_merged["Date"] = pd.to_datetime(df_merged["Date"].astype(str).str[:period_slice])

    closed_range = pd.to_datetime(df["closed_at"]).dt.to_period(interval).value_counts().sort_index()
    df_closed = closed_range.to_frame().reset_index().rename(columns={"closed_at": "Date", "count": "closed_at"})
    df_closed["Date"] = pd.to_datetime(df_closed["Date"].astype(str).str[:period_slice])

    # Merge for stacked bar chart
    df_closed_merged = pd.merge(df_merged, df_closed, on="Date", how="outer")

    # Format dates for graph generation
    if interval == "M":
        df_created["Date"] = df_created["Date"].dt.strftime("%Y-%m-01")
        df_closed_merged["Date"] = df_closed_merged["Date"].dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_created["Date"] = df_created["Date"].dt.strftime("%Y-01-01")
        df_closed_merged["Date"] = df_closed_merged["Date"].dt.strftime("%Y-01-01")

    df_closed_merged["closed_at"] = df_closed_merged["closed_at"] - df_closed_merged["merged_at"]

    # ----- Open PR processing ----
    dates = pd.date_range(start=earliest, end=latest, freq="D", inclusive="both")
    df_open = dates.to_frame(index=False, name="Date")

    # Vectorized open count calculation
    df_open["Open"] = get_open_vectorized(df, df_open["Date"])
    df_open["Date"] = df_open["Date"].dt.strftime("%Y-%m-%d")

    return df_created, df_closed_merged, df_open


def create_figure(
    df_created: pd.DataFrame,
    df_closed_merged: pd.DataFrame,
    df_open: pd.DataFrame,
    interval,
):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    fig = go.Figure()
    fig.add_bar(
        x=df_created["Date"],
        y=df_created["created_at"],
        opacity=0.9,
        hovertemplate=hover + "<br>Created: %{y}<br>" + "<extra></extra>",
        offsetgroup=0,
        marker=dict(color=baby_blue[6]),
        name="Opened",
    )
    fig.add_bar(
        x=df_closed_merged["Date"],
        y=df_closed_merged["merged_at"],
        opacity=0.9,
        hovertemplate=hover + "<br>Merged: %{y}<br>" + "<extra></extra>",
        offsetgroup=1,
        marker=dict(color=baby_blue[0]),
        name="Merged",
    )
    fig.add_bar(
        x=df_closed_merged["Date"],
        y=df_closed_merged["closed_at"],
        opacity=0.9,
        hovertemplate=[f"{hover}<br>Closed: {val}<br><extra></extra>" for val in df_closed_merged["closed_at"]],
        offsetgroup=1,
        base=df_closed_merged["merged_at"],
        marker=dict(color=baby_blue[2]),
        name="Closed",
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
        font=dict(size=14),
    )
    fig.add_trace(
        go.Scatter(
            x=df_open["Date"],
            y=df_open["Open"],
            mode="lines",
            marker=dict(color=baby_blue[8]),
            name="Open",
            hovertemplate="PRs Open: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
        )
    )

    return fig


def get_open_vectorized(df: pd.DataFrame, dates: pd.Series) -> pd.Series:
    """
    Vectorized calculation of open PRs at each date.

    For each date, counts PRs where: created_at <= date AND (closed_at > date OR closed_at is null)

    This is 10-100x faster than row-by-row .apply() for large date ranges.
    """
    import numpy as np

    # Convert to numpy arrays for faster operations
    created = df["created_at"].values
    closed = df["closed_at"].values
    dates_arr = dates.values

    # For each date, count PRs that are open
    # Open means: created before/on date AND (not closed OR closed after date)
    open_counts = []
    for date in dates_arr:
        # PRs created on or before this date
        created_mask = created <= date
        # PRs that are still open (closed is null or closed after date)
        still_open_mask = pd.isna(closed) | (closed > date)
        # Count PRs matching both conditions
        count = np.sum(created_mask & still_open_mask)
        open_counts.append(count)

    return pd.Series(open_counts, index=dates.index)
