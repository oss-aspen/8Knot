from dash import html, dcc, callback
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import time

from app import augur
from pages.utils.job_utils import nodata_graph
from queries.prs_query import prs_query as prq
from queries.pr_files_query import pr_file_query as prfq
from queries.repo_files_query import repo_files_query as rfq

from . import heatmap_utils as hu

PAGE = "codebase"
VIZ_ID = "contribution-file-heatmap"


# UI Component
graph_loading = html.Div(
    [
        dbc.Popover(
            [
                dbc.PopoverHeader("Graph Info:"),
                dbc.PopoverBody(
                    """
                    This visualization analyzes the activity of the open or merged pull requests to sub-sections
                    (files or folders) of a repository.
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
                        dbc.Label(
                            "View:",
                            html_for=f"graph-view-{PAGE}-{VIZ_ID}",
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.RadioItems(
                                id=f"graph-view-{PAGE}-{VIZ_ID}",
                                options=[
                                    {"label": "PR Opened", "value": "created"},
                                    {"label": "PR Merged", "value": "merged"},
                                ],
                                value="created",
                                inline=True,
                            ),
                            width="auto",
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

gc_contribution_file_heatmap = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contribution File Heatmap",
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
    background=True,
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
        Input(f"repo-{PAGE}-{VIZ_ID}", "value"),
        Input(f"directory-{PAGE}-{VIZ_ID}", "value"),
        Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def contribution_file_heatmap_graph(repo_id, directory, graph_view):
    """Generate the contribution file heatmap."""
    start = time.perf_counter()
    logging.info(f"{VIZ_ID} - Generating heatmap for repo {repo_id}, directory '{directory}', view '{graph_view}'")

    if repo_id is None or directory is None:
        logging.debug(f"{VIZ_ID} - Missing required parameters")
        return nodata_graph

    # Wait for all required caches
    for query_func, query_name in [(rfq, "repo_files"), (prfq, "pr_files"), (prq, "prs")]:
        if not hu.wait_for_cache(query_func.__name__, [repo_id]):
            logging.error(f"{VIZ_ID} - Cache timeout for {query_name}")
            return nodata_graph

    # Retrieve data
    df_file = hu.retrieve_cached_data(rfq.__name__, [repo_id])
    df_file_pr = hu.retrieve_cached_data(prfq.__name__, [repo_id])
    df_pr = hu.retrieve_cached_data(prq.__name__, [repo_id])

    # Validate data
    if df_file.empty or df_file_pr.empty or df_pr.empty:
        logging.info(f"{VIZ_ID} - No data available for repo {repo_id}")
        return nodata_graph

    # Process data
    df = process_data(df_file, df_file_pr, df_pr, directory, graph_view)

    if df.empty:
        return nodata_graph

    # Create figure
    color_label = "PRs Opened" if graph_view == "created" else "PRs Merged"
    fig = hu.create_heatmap_figure(df, color_label=color_label)

    logging.info(f"{VIZ_ID} - Heatmap generated in {time.perf_counter() - start:.2f}s")
    return fig


def process_data(
    df_file: pd.DataFrame,
    df_file_pr: pd.DataFrame,
    df_pr: pd.DataFrame,
    directory: str,
    graph_view: str,
) -> pd.DataFrame:
    """
    Process data for contribution file heatmap.

    Refactored to use shared utilities for DRY compliance.

    Steps:
    1. Clean file data and join with PR files
    2. Aggregate PRs by directory
    3. Map PRs to dates
    4. Create time-based matrix for heatmap
    """
    try:
        # Step 1: Prepare file dataframe
        df_file = hu.prepare_file_df(df_file)

        if df_file.empty:
            return pd.DataFrame()

        # Rename columns to match expected format (query returns different names)
        df_file_pr = df_file_pr.rename(columns={"pull_request": "pull_request_id", "id": "repo_id"})
        df_pr = df_pr.rename(
            columns={
                "pull_request": "pull_request_id",
                "created": "created_at",
                "merged": "merged_at",
                "closed": "closed_at",
            }
        )

        # Drop repo_id from file_pr
        if "repo_id" in df_file_pr.columns:
            df_file_pr = df_file_pr.drop(columns=["repo_id"])

        # Group PRs by file path
        df_file_pr_grouped = df_file_pr.groupby("file_path")["pull_request_id"].apply(list).reset_index()

        # Merge file data with PR data
        df_file = hu.safe_merge(df_file, df_file_pr_grouped, on="file_path", how="left")

        if df_file.empty:
            return pd.DataFrame()

        # Fill NaN with empty lists
        df_file = df_file.copy()
        df_file["pull_request_id"] = df_file["pull_request_id"].apply(lambda x: x if isinstance(x, list) else [])

        # Step 2: Aggregate by directory using new utility
        df_dir = hu.aggregate_ids_by_directory(df_file, directory, "pull_request_id")

        if df_dir.empty:
            return pd.DataFrame()

        # Step 3: Map PRs to dates using new utility
        date_col = "created_at" if graph_view == "created" else "merged_at"
        df_dir = hu.map_ids_to_dates(
            df_dir, df_pr, "pull_request_id", "pull_request_id", date_col, convert_to_string=False
        )

        # Remove rows with no dates (for merged view, PRs might not have merge dates)
        df_dir = df_dir.dropna(subset=["dates"])

        if df_dir.empty:
            return pd.DataFrame()

        # Step 4: Create time matrix using new utility
        result = hu.create_time_matrix(df_dir, df_pr, date_col)

        return result

    except Exception as e:
        logging.error(f"{VIZ_ID} - Error processing data: {e}")
        return pd.DataFrame()
