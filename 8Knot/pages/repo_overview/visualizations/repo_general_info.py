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
from queries.repo_info_query import repo_info_query as riq
from queries.repo_files_query import repo_files_query as rfq
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
                html.H3(
                    "Repo General Info",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dcc.Loading(
                    html.Div(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Row([dbc.Label(["Last Updated: ", html.Span(id=f"{PAGE}-{VIZ_ID}-updated")], className="mr-2")]),
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


# callback for repo general info
@callback(
    [Output(f"{PAGE}-{VIZ_ID}", "children"), Output(f"{PAGE}-{VIZ_ID}-updated", "children")],
    [
        Input("repo-info-selection", "value"),
    ],
    background=True,
)
def repo_general_info(repo):

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

    updated_times_repo_info = pd.to_datetime(df_repo_info["data_collection_date"])

    unique_updated_times = updated_times_repo_info.drop_duplicates().to_numpy().flatten()

    if len(unique_updated_times) > 1:
        logging.warning(f"{VIZ_ID} - MORE THAN ONE LAST UPDATE DATE")

    updated_date = pd.to_datetime(str(unique_updated_times[-1])).strftime("%d/%m/%Y")

    # convert to datetime objects rather than strings
    df_releases["release_published_at"] = pd.to_datetime(df_releases["release_published_at"], utc=True)

    # release information preprocessing
    # get date of previous row/previous release
    df_releases["previous_release"] = df_releases["release_published_at"].shift()
    # calculate difference
    df_releases["time_bt_release"] = df_releases["release_published_at"] - df_releases["previous_release"]
    # reformat to days
    df_releases["time_bt_release"] = df_releases["time_bt_release"].apply(lambda x: x.days)

    # release info initial assignments
    num_releases = df_releases.shape[0]
    last_release_date = df_releases["release_published_at"].max()
    avg_release_time = df_releases["time_bt_release"].abs().mean().round(1)

    # reformat based on if there are any releases
    if num_releases == 0:
        avg_release_time = "No Releases Found"
        last_release_date = "No Releases Found"
    else:
        avg_release_time = str(avg_release_time) + " Days"
        last_release_date = last_release_date.strftime("%Y-%m-%d")

    # direct varible assignment from query results
    license = df_repo_info.loc[0, "license"]
    stars_count = df_repo_info.loc[0, "stars_count"]
    fork_count = df_repo_info.loc[0, "fork_count"]
    watchers_count = df_repo_info.loc[0, "watchers_count"]
    issues_enabled = df_repo_info.loc[0, "issues_enabled"].capitalize()

    # checks for code of conduct file
    coc = df_repo_info.loc[0, "code_of_conduct_file"]
    if coc is None:
        coc = "File not found"
    else:
        coc = "File found"

    # check files for CONTRIBUTING.md
    contrib_guide = (df_repo_files["file_name"].eq("CONTRIBUTING.md")).any()
    if contrib_guide:
        contrib_guide = "File found"
    else:
        contrib_guide = "File not found"

    # keep an eye out if github changes this to be located like coc
    security_policy = (df_repo_files["file_name"].eq("SECURITY.md")).any()
    if security_policy:
        security_policy = "File found"
    else:
        security_policy = "File not found"

    # create df to hold table information
    df = pd.DataFrame(
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
                license,
                coc,
                contrib_guide,
                security_policy,
                num_releases,
                last_release_date,
                avg_release_time,
                stars_count,
                fork_count,
                watchers_count,
                issues_enabled,
            ],
        }
    )

    return df, dbc.Label(updated_date)


def multi_query_helper(repos):
    """
    hack to put all of the cache-retrieval
    in the same place temporarily
    """

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=rfq.__name__, repolist=repos):
        logging.warning(f"CONTRIBUTION FILE HEATMAP - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=riq.__name__, repolist=repos):
        logging.warning(f"CONTRIBUTION FILE HEATMAP - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=rrq.__name__, repolist=repos):
        logging.warning(f"CONTRIBUTION FILE HEATMAP - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # GET ALL DATA FROM POSTGRES CACHE
    df_file = cf.retrieve_from_cache(
        tablename=rfq.__name__,
        repolist=repos,
    )
    df_repo_info = cf.retrieve_from_cache(
        tablename=riq.__name__,
        repolist=repos,
    )
    df_releases = cf.retrieve_from_cache(
        tablename=rrq.__name__,
        repolist=repos,
    )

    return df_file, df_repo_info, df_releases
