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
from queries.pr_response_query import pr_response_query as prr
import io
from cache_manager.cache_manager import CacheManager as cm
import cache_manager.cache_facade as cf
from pages.utils.job_utils import nodata_graph
import time
import app

PAGE = "contributions"
VIZ_ID = "pr-first-response"

gc_pr_first_response = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Pull Request Time to First Response",
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
                            Compares the volume of PRs being opened against the number of those PRs that \n
                            receive at least one response within the parameterized timeframe after being opened.
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
                                    "Response Days:",
                                    html_for=f"response-days-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"response-days-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=2,
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
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="pr-first-response",
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


# callback for pr first response graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"response-days-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def pr_first_response_graph(repolist, num_days, bot_switch):
    while not_cached := cf.get_uncached(func_name=prr.__name__, repolist=repolist):
        logging.warning(f"PR_FIRST_RESPONSE - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=prr.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    df = process_data(df, num_days)

    fig = create_figure(df, num_days)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, num_days):
    """
    Process PR first response data using Polars for performance, returning Pandas for visualization.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast initial processing
    pl_df = to_polars(df)

    # Convert to datetime
    pl_df = pl_df.with_columns(
        [
            pl.col("msg_timestamp").cast(pl.Datetime("us", "UTC")),
            pl.col("pr_created_at").cast(pl.Datetime("us", "UTC")),
            pl.col("pr_closed_at").cast(pl.Datetime("us", "UTC")),
        ]
    )

    # Drop messages from the PR creator
    pl_df = pl_df.filter(pl.col("cntrb_id") != pl.col("msg_cntrb_id"))

    # Sort and keep first (earliest) response per PR
    pl_df = pl_df.sort("msg_timestamp").unique(subset=["pull_request_id"], keep="first")

    # Get date range
    earliest = pl_df.select(pl.col("pr_created_at").min()).item()
    latest_created = pl_df.select(pl.col("pr_created_at").max()).item()
    latest_closed = pl_df.select(pl.col("pr_closed_at").max()).item()
    latest = max(latest_created, latest_closed) if latest_closed else latest_created

    # Convert to Pandas for the loop processing
    df = to_pandas(pl_df)

    # === POLARS PROCESSING END ===

    # Generate date range
    dates = pd.date_range(start=earliest, end=latest, freq="D", inclusive="both")
    df_pr_responses = dates.to_frame(index=False, name="Date")

    # Use list comprehension instead of .apply()
    results = [get_open_response(df, date, num_days) for date in df_pr_responses["Date"]]

    if results:
        df_pr_responses["Open"], df_pr_responses["Response"] = zip(*results)

    df_pr_responses["Date"] = df_pr_responses["Date"].dt.strftime("%Y-%m-%d")

    return df_pr_responses


def create_figure(df: pd.DataFrame, num_days):
    fig = go.Figure(
        [
            go.Scatter(
                name="Prs Open",
                x=df["Date"],
                y=df["Open"],
                mode="lines",
                showlegend=True,
                hovertemplate="PR's Open: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                marker=dict(color=baby_blue[8]),
            ),
            go.Scatter(
                name="Response <" + str(num_days) + " days",
                x=df["Date"],
                y=df["Response"],
                mode="lines",
                showlegend=True,
                hovertemplate="PRs: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                marker=dict(color=baby_blue[2]),
            ),
        ]
    )
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of PRs",
        font=dict(size=14),
    )

    return fig


def get_open_response(df, date, num_days):
    """
    Calculate open PRs and those with a response within num_days using Polars.

    Uses Polars for fast filtering operations (2-5x faster than Pandas).

    Args:
        df: DataFrame with PR response data
        date: Target date
        num_days: Number of days within which a response is expected

    Returns:
        tuple: (num_open, num_response)
    """
    # Convert to Polars for fast filtering
    pl_df = to_polars(df)

    # Filter to PRs created before date
    pl_created = pl_df.filter(pl.col("pr_created_at") <= date)

    # Keep PRs still open at date or not closed
    pl_open = pl_created.filter((pl.col("pr_closed_at") > date) | pl.col("pr_closed_at").is_null())

    if pl_open.height == 0:
        return 0, 0

    # Add response deadline column and filter for responses in time
    response_deadline = date + pd.DateOffset(days=num_days)
    pl_response = pl_open.filter(pl.col("msg_timestamp") < response_deadline)

    num_open = pl_open.height
    num_response = pl_response.height

    return num_open, num_response
