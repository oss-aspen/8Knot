from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import polars as pl
import logging
from dateutil.relativedelta import *  # type: ignore
from pages.utils.polars_utils import to_polars, to_pandas
from queries.ossf_score_query import ossf_score_query as osq
import io
import cache_manager.cache_facade as cf
from pages.utils.job_utils import nodata_graph
import time
from datetime import datetime

PAGE = "repo_info"
VIZ_ID = "ossf-scorecard"

gc_ossf_scorecard = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "OSSF Scorecard",
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
                        dbc.PopoverHeader("Link to details about checks:"),
                        dbc.PopoverBody("https://github.com/ossf/scorecard?tab=readme-ov-file#what-is-scorecard"),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    html.Div(id=f"{PAGE}-{VIZ_ID}", style={"marginTop": "20px"}),
                ),
                html.Hr(className="card-split"),  # Divider between graph and controls
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    ["Last Updated: ", html.Span(id=f"{PAGE}-{VIZ_ID}-updated")],
                                    width={"size": "auto"},
                                ),
                            ],
                            justify="start",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        ),
    ],
    className="dark-card",
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


# callback for ossf scorecard
@callback(
    [Output(f"{PAGE}-{VIZ_ID}", "children"), Output(f"{PAGE}-{VIZ_ID}-updated", "children")],
    [
        Input("repo-info-selection", "value"),
    ],
    background=True,
)
def ossf_scorecard(repo: str):

    if repo is not None:
        repo = int(repo)

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=osq.__name__, repolist=[repo]):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=osq.__name__,
        repolist=[repo],
    )

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True), dbc.Label("No data")

    # Process data using Polars, return Pandas for visualization
    df_result, updated_date = process_data(df)

    table = dbc.Table.from_dataframe(df_result, striped=True, bordered=True, hover=True)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return table, dbc.Label(updated_date)


def process_data(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    Process OSSF scorecard data using Polars for performance, returning Pandas for visualization.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast processing
    pl_df = to_polars(df)

    # Get last update date
    updated_times = pl_df.select(pl.col("data_collection_date").cast(pl.Datetime)).unique()
    if updated_times.height > 1:
        logging.warning(f"{VIZ_ID} - MORE THAN ONE DATA COLLECTION DATE")
    updated_date = updated_times.row(-1)[0].strftime("%d/%m/%Y") if updated_times.height > 0 else "Unknown"

    # Drop unnecessary columns
    pl_df = pl_df.drop(["repo_id", "data_collection_date"])

    # Rename aggregate score and sort
    pl_df = pl_df.with_columns(
        pl.when(pl.col("name") == "OSSF_SCORECARD_AGGREGATE_SCORE")
        .then(pl.lit("Aggregate Score"))
        .otherwise(pl.col("name"))
        .alias("name")
    )

    pl_df = pl_df.sort("name")

    # Rename columns for display
    pl_df = pl_df.rename({"name": "Check Type", "score": "Score"})

    # === POLARS PROCESSING END ===

    # Convert to Pandas at the visualization boundary
    return to_pandas(pl_df), updated_date
