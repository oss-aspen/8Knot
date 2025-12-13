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
from pages.utils.graph_utils import get_graph_time_values, color_seq
from pages.utils.polars_utils import to_polars, to_pandas
from queries.repo_info_query import repo_info_query as riq

# from queries.repo_files_query import repo_files_query as rfq #TODO: run back on when the query hang is fixed
from queries.repo_releases_query import repo_releases_query as rrq
import io
import cache_manager.cache_facade as cf
from pages.utils.job_utils import nodata_graph
import time
from datetime import datetime

PAGE = "repo_info"
VIZ_ID = "repo-general-info"

gc_repo_general_info = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    dbc.Col(
                        html.H3(
                            "Repo General Info",
                            className="card-title",
                        ),
                    ),
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


# callback for repo general info
@callback(
    [Output(f"{PAGE}-{VIZ_ID}", "children"), Output(f"{PAGE}-{VIZ_ID}-updated", "children")],
    [
        Input("repo-info-selection", "value"),
    ],
    background=True,
)
def repo_general_info(repo):

    if repo is not None:
        repo = int(repo)

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # get dataframes of data from cache
    df_repo_files, df_repo_info, df_releases = multi_query_helper([repo])

    # test if there is data
    if df_repo_files.empty and df_repo_info.empty and df_releases.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return dbc.Table.from_dataframe(pd.DataFrame(), striped=True, bordered=True, hover=True), dbc.Label("No data")

    df, last_updated = process_data(df_repo_files, df_repo_info, df_releases)

    table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return table, last_updated


def process_data(df_repo_files, df_repo_info, df_releases):
    """
    Process repository data using Polars for performance, returning Pandas for visualization.

    This follows the "Polars Core, Pandas Edge" architecture:
    - Core processing in Polars (2-10x faster)
    - Return Pandas DataFrame for Plotly/Dash compatibility
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast processing
    pl_repo_info = to_polars(df_repo_info)
    pl_releases = to_polars(df_releases) if not df_releases.empty else pl.DataFrame()
    pl_files = to_polars(df_repo_files) if not df_repo_files.empty else pl.DataFrame()

    # Get last update date
    updated_times = pl_repo_info.select(pl.col("data_collection_date").cast(pl.Datetime)).unique()
    if updated_times.height > 1:
        logging.warning(f"{VIZ_ID} - MORE THAN ONE LAST UPDATE DATE")
    updated_date = updated_times.row(-1)[0].strftime("%d/%m/%Y") if updated_times.height > 0 else "Unknown"

    # Release information processing with Polars
    if pl_releases.height > 0:
        pl_releases = pl_releases.with_columns(pl.col("release_published_at").cast(pl.Datetime("us", "UTC")))
        pl_releases = pl_releases.with_columns(pl.col("release_published_at").shift(1).alias("previous_release"))
        pl_releases = pl_releases.with_columns(
            (pl.col("release_published_at") - pl.col("previous_release")).dt.total_days().alias("time_bt_release")
        )

        num_releases = pl_releases.height
        last_release_date = pl_releases.select(pl.col("release_published_at").max()).item()
        avg_release_time = pl_releases.select(pl.col("time_bt_release").abs().mean()).item()

        if avg_release_time is not None:
            avg_release_time = f"{round(avg_release_time, 1)} Days"
        else:
            avg_release_time = "No Releases Found"
        last_release_date = last_release_date.strftime("%Y-%m-%d") if last_release_date else "No Releases Found"
    else:
        num_releases = 0
        avg_release_time = "No Releases Found"
        last_release_date = "No Releases Found"

    # Extract repo info values using Polars
    repo_info_row = pl_repo_info.row(0, named=True)
    license_val = repo_info_row["license"]
    stars_count = repo_info_row["stars_count"]
    fork_count = repo_info_row["fork_count"]
    watchers_count = repo_info_row["watchers_count"]
    issues_enabled = str(repo_info_row["issues_enabled"]).capitalize()

    # Check for code of conduct file
    coc = repo_info_row["code_of_conduct_file"]
    coc = "File found" if coc is not None else "File not found"

    # Check files for CONTRIBUTING.md and SECURITY.md using Polars
    if pl_files.height > 0:
        contrib_guide = pl_files.filter(pl.col("file_name") == "CONTRIBUTING.md").height > 0
        security_policy = pl_files.filter(pl.col("file_name") == "SECURITY.md").height > 0
    else:
        contrib_guide = False
        security_policy = False

    contrib_guide = "File found" if contrib_guide else "File not found"
    security_policy = "File found" if security_policy else "File not found"

    # === POLARS PROCESSING END ===

    # Create final DataFrame in Polars, then convert to Pandas for visualization
    pl_result = pl.DataFrame(
        {
            "Section": [
                "License",
                "Code of Conduct",
                "Contributor Guidelines",
                "Security Policy",
                "Number of Releases",
                "Last Release Date",
                "Avg Time Between Releases",
                "Star Count",
                "Fork Count",
                "Watcher Count",
                "Issues Enabled",
            ],
            "Info": [
                str(license_val) if license_val else "Unknown",
                coc,
                contrib_guide,
                security_policy,
                str(num_releases),
                last_release_date,
                avg_release_time,
                str(stars_count),
                str(fork_count),
                str(watchers_count),
                issues_enabled,
            ],
        }
    )

    # Convert to Pandas at the visualization boundary
    return to_pandas(pl_result), dbc.Label(updated_date)


def multi_query_helper(repos: list[int]):
    """
    hack to put all of the cache-retrieval
    in the same place temporarily
    """

    # wait for data to asynchronously download and become available.
    """while not_cached := cf.get_uncached(func_name=rfq.__name__, repolist=repos):
        logging.warning(f"REPO GENERAL INFO - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)"""  # comment out until query is fixed

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=riq.__name__, repolist=repos):
        logging.warning(f"REPO GENERAL INFO - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=rrq.__name__, repolist=repos):
        logging.warning(f"REPO GENERAL INFO - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # GET ALL DATA FROM POSTGRES CACHE
    """df_file = cf.retrieve_from_cache(
        tablename=rfq.__name__,
        repolist=repos,
    )"""
    df_file = pd.DataFrame(columns=["file_path", "file_name", "id"])  # comment out until query is fixed
    df_repo_info = cf.retrieve_from_cache(
        tablename=riq.__name__,
        repolist=repos,
    )
    df_releases = cf.retrieve_from_cache(
        tablename=rrq.__name__,
        repolist=repos,
    )

    return df_file, df_repo_info, df_releases
