from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import polars as pl
import logging
import numpy as np
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from pages.utils.job_utils import nodata_graph
from queries.contributors_query import contributors_query as ctq
import time
import io
from cache_manager.cache_manager import CacheManager as cm
import app
import pages.utils.preprocessing_utils as preproc_utils
import cache_manager.cache_facade as cf

PAGE = "contributors"
VIZ_ID = "contrib-types-over-time"

gc_contributors_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Contributor Types Over Time",
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
                            Visualizes the per-quarter consistency of contributors.\n
                            Partitions quarterly population of contributors based on whether they make\n
                            'Required Contributions' or more contributions.
                            Please read definition of 'Contributor Consistency' on Info page.
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
                                    "Contributions Required:",
                                    html_for=f"contributions-required-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"contributions-required-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=15,
                                        step=1,
                                        value=4,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
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
    id="contributor-types",
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
    [
        Input("repo-choices", "data"),
        Input(f"contributions-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def create_contrib_over_time_graph(repolist, contribs, interval, bot_switch):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=ctq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=ctq.__name__,
        repolist=repolist,
    )

    df = preproc_utils.contributors_df_action_naming(df)

    # test if there is data
    if df.empty:
        logging.warning("PULL REQUESTS OVER TIME - NO DATA AVAILABLE")
        return nodata_graph

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # function for all data pre processing
    df_drive_repeat = process_data(df, interval, contribs)

    fig = create_figure(df_drive_repeat, interval)

    logging.warning(f"CONTRIBUTIONS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df, interval, contribs):
    """
    Process contributor types over time data using Polars for performance.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast processing
    pl_df = to_polars(df)

    # Convert to datetime and drop nulls
    pl_df = pl_df.with_columns(pl.col("created_at").cast(pl.Datetime("us", "UTC")))
    pl_df = pl_df.drop_nulls()

    # Get contributors with specified rank
    contributors = pl_df.filter(pl.col("rank") == contribs).select("cntrb_id").unique().to_series().to_list()
    contributors_set = set(contributors)

    # Split into drive-by and repeat contributors
    pl_drive = pl_df.filter(~pl.col("cntrb_id").is_in(contributors_set))
    pl_repeat = pl_df.filter(pl.col("cntrb_id").is_in(contributors_set))

    # Map interval to Polars truncation format
    interval_map = {"D": "1d", "W": "1w", "M": "1mo", "Y": "1y"}
    polars_interval = interval_map.get(interval, "1mo")

    # Count unique drive-by contributors per period
    if pl_drive.height > 0:
        pl_drive_result = (
            pl_drive.with_columns(pl.col("created_at").dt.truncate(polars_interval).alias("Date"))
            .group_by("Date")
            .agg(pl.col("cntrb_id").n_unique().alias("Drive"))
        )
    else:
        pl_drive_result = pl.DataFrame({"Date": [], "Drive": []})

    # Count unique repeat contributors per period
    if pl_repeat.height > 0:
        pl_repeat_result = (
            pl_repeat.with_columns(pl.col("created_at").dt.truncate(polars_interval).alias("Date"))
            .group_by("Date")
            .agg(pl.col("cntrb_id").n_unique().alias("Repeat"))
        )
    else:
        pl_repeat_result = pl.DataFrame({"Date": [], "Repeat": []})

    # Join drive and repeat data
    if pl_drive_result.height > 0 and pl_repeat_result.height > 0:
        pl_result = pl_drive_result.join(pl_repeat_result, on="Date", how="full").sort("Date")
    elif pl_drive_result.height > 0:
        pl_result = pl_drive_result.with_columns(pl.lit(None).cast(pl.UInt32).alias("Repeat")).sort("Date")
    elif pl_repeat_result.height > 0:
        pl_result = pl_repeat_result.with_columns(pl.lit(None).cast(pl.UInt32).alias("Drive")).sort("Date")
    else:
        pl_result = pl.DataFrame({"Date": [], "Drive": [], "Repeat": []})

    # === POLARS PROCESSING END ===

    # Convert to Pandas for visualization
    df_drive_repeat = to_pandas(pl_result)

    # Format dates for graph generation
    if interval == "M":
        df_drive_repeat["Date"] = df_drive_repeat["Date"].dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_drive_repeat["Date"] = df_drive_repeat["Date"].dt.strftime("%Y-01-01")

    return df_drive_repeat


def create_figure(df_drive_repeat, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    fig = px.bar(
        df_drive_repeat,
        x="Date",
        y=["Repeat", "Drive"],
        labels={"x": x_name, "y": "Contributors"},
        color_discrete_sequence=[baby_blue[6], baby_blue[8]],
    )
    fig.update_traces(
        hovertemplate=hover + "<br>Contributors: %{y}<br><extra></extra>",
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
        legend_title_text="Type",
        yaxis_title="Number of Contributors",
        margin_b=40,
        font=dict(size=14),
    )

    return fig
