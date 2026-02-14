from dash import html, dcc, callback
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import time

from app import augur
import app
from pages.utils.job_utils import nodata_graph
from queries.contributors_query import contributors_query as cnq
from queries.cntrb_per_file_query import cntrb_per_file_query as cpfq
from queries.repo_files_query import repo_files_query as rfq
import pages.utils.preprocessing_utils as preproc_u

from . import heatmap_utils as hu

PAGE = "codebase"
VIZ_ID = "reviewer-file-heatmap"


# UI Component
graph_loading = html.Div(
    [
        dbc.Popover(
            [
                dbc.PopoverHeader("Graph Info:"),
                dbc.PopoverBody(
                    """
                    This visualization analyzes the activity of the reviewers to sub-sections (files or folders)
                    of a repository. Specifically, this heatmap identifies the last time a sub-section's reviewer
                    (those people who have reviewed at least one pull request to a sub-section) last contributed to the
                    repository. See the definition of "contribution" on the Info page for more information. This could be
                    interpreted as monitoring technical knowledge retention of codebase components: if a sub-section's
                    past reviewers are no longer active in the repository, maintainership of that sub-section could
                    be insufficient and require attention.
                    """
                ),
            ],
            id=f"popover-{PAGE}-{VIZ_ID}",
            target=f"popover-target-{PAGE}-{VIZ_ID}",
            placement="top",
            is_open=False,
        ),
        dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
        dbc.Form(
            [
                dbc.Row(
                    [
                        dbc.Label(
                            "Repository:",
                            html_for=f"repo-{PAGE}-{VIZ_ID}",
                            width="auto",
                        ),
                        dbc.Col(
                            dmc.Select(
                                id=f"repo-{PAGE}-{VIZ_ID}",
                                placeholder="Select Repository",
                                classNames={"values": "dmc-multiselect-custom"},
                                searchable=True,
                                clearable=True,
                            ),
                            className="me-2",
                            width=3,
                        ),
                        dbc.Label(
                            "Directory:",
                            html_for=f"directory-{PAGE}-{VIZ_ID}",
                            width="auto",
                        ),
                        dbc.Col(
                            dmc.Select(
                                id=f"directory-{PAGE}-{VIZ_ID}",
                                classNames={"values": "dmc-multiselect-custom"},
                                searchable=True,
                                clearable=False,
                                value="Top Level Directory",
                            ),
                            className="me-2",
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                color="secondary",
                                size="sm",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    className="g-2",
                ),
            ]
        ),
    ],
)

gc_reviewer_file_heatmap = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Reviewer File Heatmap",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dcc.Loading(children=graph_loading),
            ]
        )
    ],
)


# Callbacks
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
    [
        Output(f"repo-{PAGE}-{VIZ_ID}", "data"),
        Output(f"repo-{PAGE}-{VIZ_ID}", "value"),
    ],
    [Input("repo-choices", "data")],
)
def repo_dropdown(repo_ids):
    """Populate repository dropdown."""
    logging.debug(f"{VIZ_ID} - repo_dropdown called with {len(repo_ids) if repo_ids else 0} repos")
    return hu.build_repo_dropdown_data(repo_ids, rfq)


@callback(
    [
        Output(f"directory-{PAGE}-{VIZ_ID}", "data"),
        Output(f"directory-{PAGE}-{VIZ_ID}", "value"),
    ],
    [Input(f"repo-{PAGE}-{VIZ_ID}", "value")],
)
def directory_dropdown(repo_id):
    """Populate directory dropdown based on selected repository."""
    logging.debug(f"{VIZ_ID} - Loading directories for repo_id={repo_id}")
    if repo_id is None:
        return [hu.TOP_LEVEL_DIRECTORY], hu.TOP_LEVEL_DIRECTORY

    # Wait for cache with timeout
    if not hu.wait_for_cache(rfq.__name__, [repo_id]):
        logging.error(f"{VIZ_ID} - Cache timeout for repo {repo_id}")
        return [hu.TOP_LEVEL_DIRECTORY], hu.TOP_LEVEL_DIRECTORY

    # Retrieve file data
    df = hu.retrieve_cached_data(rfq.__name__, [repo_id])

    if df.empty:
        logging.info(f"{VIZ_ID} - No file data available for repo {repo_id}")
        return [hu.TOP_LEVEL_DIRECTORY], hu.TOP_LEVEL_DIRECTORY

    # Prepare file dataframe and extract directories
    df = hu.prepare_file_df(df)
    directories = hu.get_directories(df)

    logging.debug(f"{VIZ_ID} - Found {len(directories)} directories")
    return directories, hu.TOP_LEVEL_DIRECTORY


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"repo-{PAGE}-{VIZ_ID}", "value"),
        Input(f"directory-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def reviewer_file_heatmap_graph(searchbar_repos, repo_id, directory, bot_switch):
    """Generate the reviewer file heatmap."""
    start = time.perf_counter()
    logging.info(f"{VIZ_ID} - Generating heatmap for repo {repo_id}, directory '{directory}'")

    if repo_id is None or directory is None:
        logging.debug(f"{VIZ_ID} - Missing required parameters")
        return nodata_graph

    # Wait for all required caches
    for query_func, query_name, repos in [
        (rfq, "repo_files", [repo_id]),
        (cnq, "contributors", searchbar_repos),
        (cpfq, "cntrb_per_file", [repo_id]),
    ]:
        if not hu.wait_for_cache(query_func.__name__, repos):
            logging.error(f"{VIZ_ID} - Cache timeout for {query_name}")
            return nodata_graph

    # Retrieve data
    df_file = hu.retrieve_cached_data(rfq.__name__, [repo_id])
    df_actions = hu.retrieve_cached_data(cnq.__name__, searchbar_repos)
    df_file_cntrbs = hu.retrieve_cached_data(cpfq.__name__, [repo_id])

    # Validate data
    if df_file.empty or df_actions.empty or df_file_cntrbs.empty:
        logging.info(f"{VIZ_ID} - No data available for repo {repo_id}")
        return nodata_graph

    # Apply preprocessing
    df_actions = preproc_u.contributors_df_action_naming(df_actions)
    df_file_cntrbs = preproc_u.cntrb_per_file(df_file_cntrbs)

    # Process data
    df = process_data(df_file, df_actions, df_file_cntrbs, directory, bot_switch)

    if df.empty:
        return nodata_graph

    # Create figure
    fig = hu.create_heatmap_figure(df, color_label="Reviewers")

    logging.info(f"{VIZ_ID} - Heatmap generated in {time.perf_counter() - start:.2f}s")
    return fig


def process_data(
    df_file: pd.DataFrame,
    df_actions: pd.DataFrame,
    df_file_cntrbs: pd.DataFrame,
    directory: str,
    bot_switch: bool,
) -> pd.DataFrame:
    """
    Process data for reviewer file heatmap.

    Refactored to use shared utilities for DRY compliance.

    Steps:
    1. Clean file data and join with reviewer data
    2. Aggregate reviewers by directory
    3. Map reviewers to their last activity dates
    4. Create time-based matrix for heatmap
    """
    try:
        # Step 1: Prepare file dataframe
        df_file = hu.prepare_file_df(df_file)

        if df_file.empty:
            return pd.DataFrame()

        # Clean reviewer data - drop unnecessary columns
        df_file_cntrbs = df_file_cntrbs.copy()
        if "repo_id" in df_file_cntrbs.columns:
            df_file_cntrbs = df_file_cntrbs.drop(columns=["repo_id"])
        if "cntrb_ids" in df_file_cntrbs.columns:
            df_file_cntrbs = df_file_cntrbs.drop(columns=["cntrb_ids"])

        # Merge file data with reviewer data
        df_file = hu.safe_merge(df_file, df_file_cntrbs, on="file_path", how="left")

        if df_file.empty:
            return pd.DataFrame()

        # Fill NaN with empty lists and filter bots using utility
        df_file = df_file.copy()
        df_file["reviewer_ids"] = df_file["reviewer_ids"].apply(
            lambda x: hu.filter_bots_from_ids(x if isinstance(x, list) else [], bot_switch)
        )

        # Step 2: Aggregate by directory using new utility
        df_dir = hu.aggregate_ids_by_directory(df_file, directory, "reviewer_ids")

        if df_dir.empty:
            return pd.DataFrame()

        # Step 3: Map reviewers to last activity using new utility
        # First get last activity per reviewer
        df_actions_copy = df_actions.copy()
        df_actions_copy["created_at"] = pd.to_datetime(df_actions_copy["created_at"], utc=True)
        df_last = df_actions_copy.sort_values(by="created_at", ascending=False).drop_duplicates(
            subset="cntrb_id", keep="first"
        )

        df_dir = hu.map_ids_to_dates(df_dir, df_last, "reviewer_ids", "cntrb_id", "created_at")

        if df_dir.empty:
            return pd.DataFrame()

        # Step 4: Create time matrix using new utility
        result = hu.create_time_matrix(df_dir, df_actions, "created_at", filter_action="PR Opened")

        return result

    except Exception as e:
        logging.error(f"{VIZ_ID} - Error processing data: {e}")
        return pd.DataFrame()
