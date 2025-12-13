from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import polars as pl
import logging
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from queries.commits_query import commits_query as cmq
from pages.utils.job_utils import nodata_graph
import time
import cache_manager.cache_facade as cf

PAGE = "contributions"
VIZ_ID = "commits-over-time"

gc_commits_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Commits Over Time",
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
                            Visualizes the number of commits added to the project.\n
                            Commits are counted relative to a user-selected time window.
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
                                    "Date Interval:",
                                    html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
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
                            justify="start",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="commits-over-time",
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


# callback for commits over time graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def commits_over_time_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=cmq.__name__, repolist=repolist):
        logging.warning(f"COMMITS_OVER_TIME_VIZ - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # data ready.
    start = time.perf_counter()
    logging.warning("COMMITS_OVER_TIME_VIZ - START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=cmq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning("COMMITS OVER TIME - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df_created = process_data(df, interval)

    fig = create_figure(df_created, interval)

    logging.warning(f"COMMITS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval) -> pd.DataFrame:
    """
    Process commit data using Polars for performance, returning Pandas for visualization.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast processing
    pl_df = to_polars(df)

    # Convert to datetime and rename column
    pl_df = pl_df.with_columns(pl.col("author_date").cast(pl.Datetime("us", "UTC")).alias("created_at"))

    # For period-based grouping, we need to truncate dates appropriately
    # Polars has truncate which is similar to Pandas period
    if interval == "D":
        pl_df = pl_df.with_columns(pl.col("created_at").dt.truncate("1d").alias("Date"))
    elif interval == "W":
        pl_df = pl_df.with_columns(pl.col("created_at").dt.truncate("1w").alias("Date"))
    elif interval == "M":
        pl_df = pl_df.with_columns(pl.col("created_at").dt.truncate("1mo").alias("Date"))
    elif interval == "Y":
        pl_df = pl_df.with_columns(pl.col("created_at").dt.truncate("1y").alias("Date"))

    # Count unique commits per period using Polars (faster than Pandas groupby)
    pl_result = pl_df.group_by("Date").agg(pl.col("commit_hash").n_unique()).sort("Date")

    # === POLARS PROCESSING END ===

    # Convert to Pandas at the visualization boundary
    return to_pandas(pl_result)


def create_figure(df_created: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph geration
    fig = px.bar(
        df_created,
        x="Date",
        y="commit_hash",
        range_x=x_r,
        labels={"x": x_name, "y": "Commits"},
        color_discrete_sequence=[baby_blue[3]],
    )
    fig.update_traces(hovertemplate=hover + "<br>Commits: %{y}<br>")
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        rangeslider_yaxis_rangemode="match",
        range=x_r,
    )
    fig.update_layout(
        xaxis_title=x_name,
        yaxis_title="Number of Commits",
        margin_b=40,
        margin_r=20,
        font=dict(size=14),
    )

    return fig
