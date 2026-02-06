"""
Contribution File Heatmap Visualization

Shows PR activity (opened/merged) per file/directory over time.
"""

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
                    This visualization analyzes the activity of pull requests to sub-sections
                    (files or folders) of a repository over time. The heatmap shows the number
                    of PRs opened or merged for each file/directory by month.
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
    if not repo_ids:
        return [], None

    data_array = []
    for repo_id in repo_ids:
        try:
            label = augur.repo_id_to_git(repo_id)
            data_array.append({"value": repo_id, "label": label})
        except Exception as e:
            logging.warning(f"Error getting repo label for {repo_id}: {e}")
            data_array.append({"value": repo_id, "label": str(repo_id)})

    # Find first repo with valid metadata (non-empty repo_name and repo_path)
    default_repo = None
    for repo_id in repo_ids:
        df = hu.retrieve_cached_data(rfq.__name__, [repo_id])
        if not df.empty:
            repo_name = df["repo_name"].iloc[0] if "repo_name" in df.columns else None
            repo_path = df["repo_path"].iloc[0] if "repo_path" in df.columns else None
            if repo_name and repo_path:  # Skip empty strings and None
                default_repo = repo_id
                break

    if default_repo is None:
        default_repo = repo_ids[0] if repo_ids else None

    return data_array, default_repo


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
    if repo_id is None:
        return ["Top Level Directory"], "Top Level Directory"

    # Wait for cache with timeout
    if not hu.wait_for_cache(rfq.__name__, [repo_id]):
        return ["Top Level Directory"], "Top Level Directory"

    # Retrieve file data
    df = hu.retrieve_cached_data(rfq.__name__, [repo_id])

    if df.empty:
        logging.warning(f"{VIZ_ID} DROPDOWN - NO DATA AVAILABLE")
        return ["Top Level Directory"], "Top Level Directory"

    # Prepare file dataframe and extract directories
    df = hu.prepare_file_df(df)
    directories = hu.get_directories(df)

    return directories, "Top Level Directory"


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
    logging.warning(f"{VIZ_ID} - START")
    logging.warning(f"{VIZ_ID} - repo_id={repo_id}, directory={directory}")

    if repo_id is None or directory is None:
        logging.warning(f"{VIZ_ID} - EARLY RETURN: repo_id is None or directory is None")
        return nodata_graph

    # Wait for all required caches
    for query_func in [rfq, prfq, prq]:
        if not hu.wait_for_cache(query_func.__name__, [repo_id]):
            logging.warning(f"{VIZ_ID} - CACHE TIMEOUT for {query_func.__name__}")
            return nodata_graph

    # Retrieve data
    df_file = hu.retrieve_cached_data(rfq.__name__, [repo_id])
    df_file_pr = hu.retrieve_cached_data(prfq.__name__, [repo_id])
    df_pr = hu.retrieve_cached_data(prq.__name__, [repo_id])

    # Validate data
    if df_file.empty or df_file_pr.empty or df_pr.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # Process data
    df = process_data(df_file, df_file_pr, df_pr, directory, graph_view)

    if df.empty:
        return nodata_graph

    # Create figure
    color_label = "PRs Opened" if graph_view == "created" else "PRs Merged"
    fig = hu.create_heatmap_figure(df, color_label=color_label)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start:.2f}s")
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

        # Step 2: Aggregate by directory
        df_dir = aggregate_prs_by_directory(df_file, directory)

        if df_dir.empty:
            return pd.DataFrame()

        # Step 3: Map PRs to dates
        df_dir = map_prs_to_dates(df_dir, df_pr, graph_view)

        if df_dir.empty:
            return pd.DataFrame()

        # Step 4: Create time matrix
        result = create_time_matrix(df_dir, df_pr, graph_view)

        return result

    except Exception as e:
        logging.error(f"Error processing data: {e}")
        return pd.DataFrame()


def aggregate_prs_by_directory(df_file: pd.DataFrame, directory: str) -> pd.DataFrame:
    """Aggregate PRs by directory level."""
    try:
        # Determine directory level
        level = directory.count("/")
        if directory == "Top Level Directory":
            level = -1
            directory = ""

        # Filter to files in selected directory
        df_filtered = df_file[df_file["file_path"].str.startswith(directory, na=False)]

        if df_filtered.empty:
            return pd.DataFrame()

        # Check if any PRs exist
        if "pull_request_id" not in df_filtered.columns or df_filtered["pull_request_id"].isna().all():
            return pd.DataFrame()

        # Get group column
        group_column = level + 1

        if group_column not in df_filtered.columns:
            return pd.DataFrame()

        # Fill NaN with empty lists
        df_filtered = df_filtered.copy()
        df_filtered["pull_request_id"] = df_filtered["pull_request_id"].apply(
            lambda x: x if isinstance(x, list) else []
        )

        # Group and aggregate
        result = (
            df_filtered.groupby(group_column)["pull_request_id"]
            .sum()
            .reset_index()
            .rename(columns={group_column: "directory_value"})
        )

        # Convert to sets to remove duplicates
        result["pull_request_id"] = result["pull_request_id"].apply(lambda x: set(x) if isinstance(x, list) else set())

        # Filter out empty sets
        result = result[result["pull_request_id"].apply(len) > 0]

        return result

    except Exception as e:
        logging.error(f"Error aggregating PRs by directory: {e}")
        return pd.DataFrame()


def map_prs_to_dates(df_dir: pd.DataFrame, df_pr: pd.DataFrame, graph_view: str) -> pd.DataFrame:
    """Map PRs to their dates based on graph view."""
    try:
        # Convert dates
        date_col = "created_at" if graph_view == "created" else "merged_at"

        df_pr = df_pr.copy()
        df_pr[date_col] = pd.to_datetime(df_pr[date_col], utc=True)

        # Create PR to date mapping
        pr_dates = df_pr.set_index("pull_request_id")[date_col].to_dict()

        # Map PRs to dates
        df_dir = df_dir.copy()
        df_dir["dates"] = df_dir["pull_request_id"].apply(
            lambda prs: [pr_dates.get(pr) for pr in prs if pr in pr_dates and pd.notna(pr_dates.get(pr))]
        )

        # Explode dates
        df_dir = df_dir.explode("dates")

        # Remove rows with no dates
        df_dir = df_dir.dropna(subset=["dates"])

        return df_dir

    except Exception as e:
        logging.error(f"Error mapping PRs to dates: {e}")
        return pd.DataFrame()


def create_time_matrix(df_dir: pd.DataFrame, df_pr: pd.DataFrame, graph_view: str) -> pd.DataFrame:
    """Create time-based matrix for heatmap."""
    try:
        date_col = "created_at" if graph_view == "created" else "merged_at"

        # Get date range
        df_pr = df_pr.copy()
        df_pr[date_col] = pd.to_datetime(df_pr[date_col], utc=True)

        min_date = df_pr[date_col].min()
        max_date = df_pr[date_col].max()

        if pd.isna(min_date) or pd.isna(max_date):
            return pd.DataFrame()

        # Create filler dates
        df_fill = hu.create_time_range_df(min_date, max_date, "dates")

        # Combine with data
        df_combined = pd.concat([df_dir[["directory_value", "dates"]], df_fill], axis=0)
        df_combined["directory_value"] = df_combined["directory_value"].astype(str)

        # Group by month and count
        result = df_combined.groupby(pd.Grouper(key="dates", freq="1M"))["directory_value"].value_counts().unstack(0)

        # Remove "nan" row if exists
        if "nan" in result.index:
            result = result.drop("nan")

        return result

    except Exception as e:
        logging.error(f"Error creating time matrix: {e}")
        return pd.DataFrame()
