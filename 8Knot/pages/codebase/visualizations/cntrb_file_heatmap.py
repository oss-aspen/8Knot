"""
Contributor File Heatmap Visualization

Shows when contributors who touched files were last active in the repository.
"""

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
VIZ_ID = "cntrb-file-heatmap"


# UI Component
graph_loading = html.Div(
    [
        dbc.Popover(
            [
                dbc.PopoverHeader("Graph Info:"),
                dbc.PopoverBody(
                    """
                    This visualization analyzes when contributors to each file/directory
                    were last active in the repository. A contributor is someone who has
                    opened at least one pull request touching a file. The heatmap shows
                    the count of contributors whose last activity falls in each month.
                    This helps identify files where past contributors may no longer be
                    actively maintaining the code.
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

gc_cntrb_file_heatmap = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor File Heatmap",
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
    logging.warning(f"{VIZ_ID} - repo_dropdown called with repo_ids: {repo_ids}")
    if not repo_ids:
        logging.warning(f"{VIZ_ID} - repo_dropdown returning empty - no repo_ids")
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
                logging.warning(f"{VIZ_ID} - Selected default repo {default_repo} with valid metadata")
                break

    if default_repo is None:
        default_repo = repo_ids[0] if repo_ids else None
        logging.warning(f"{VIZ_ID} - No repo with valid metadata found, using first repo: {default_repo}")

    logging.warning(f"{VIZ_ID} - repo_dropdown returning {len(data_array)} repos, default={default_repo}")
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
    logging.warning(f"{VIZ_ID} - directory_dropdown called with repo_id={repo_id}")
    if repo_id is None:
        logging.warning(f"{VIZ_ID} - directory_dropdown returning default (repo_id is None)")
        return ["Top Level Directory"], "Top Level Directory"

    # Wait for cache with timeout
    if not hu.wait_for_cache(rfq.__name__, [repo_id]):
        logging.warning(f"{VIZ_ID} - directory_dropdown cache timeout")
        return ["Top Level Directory"], "Top Level Directory"

    # Retrieve file data
    df = hu.retrieve_cached_data(rfq.__name__, [repo_id])

    if df.empty:
        logging.warning(f"{VIZ_ID} DROPDOWN - NO DATA AVAILABLE")
        return ["Top Level Directory"], "Top Level Directory"

    # Prepare file dataframe and extract directories
    df = hu.prepare_file_df(df)
    directories = hu.get_directories(df)

    logging.warning(f"{VIZ_ID} - directory_dropdown returning {len(directories)} directories")
    return directories, "Top Level Directory"


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input(f"repo-{PAGE}-{VIZ_ID}", "value"),
        Input(f"directory-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def cntrb_file_heatmap_graph(repo_id, directory, bot_switch):
    """Generate the contributor file heatmap."""
    start = time.perf_counter()
    logging.warning(f"{VIZ_ID} - START")
    logging.warning(f"{VIZ_ID} - repo_id={repo_id}, directory={directory}")

    if repo_id is None or directory is None:
        logging.warning(f"{VIZ_ID} - EARLY RETURN: repo_id is None or directory is None")
        return nodata_graph

    # Wait for all required caches
    if not hu.wait_for_cache(rfq.__name__, [repo_id]):
        return nodata_graph
    if not hu.wait_for_cache(cnq.__name__, [repo_id]):
        return nodata_graph
    if not hu.wait_for_cache(cpfq.__name__, [repo_id]):
        return nodata_graph

    # Retrieve data
    df_file = hu.retrieve_cached_data(rfq.__name__, [repo_id])
    df_actions = hu.retrieve_cached_data(cnq.__name__, [repo_id])
    df_file_cntrbs = hu.retrieve_cached_data(cpfq.__name__, [repo_id])

    # Validate data
    if df_file.empty or df_actions.empty or df_file_cntrbs.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # Apply preprocessing
    df_actions = preproc_u.contributors_df_action_naming(df_actions)
    df_file_cntrbs = preproc_u.cntrb_per_file(df_file_cntrbs)

    # Process data
    df = process_data(df_file, df_actions, df_file_cntrbs, directory, bot_switch)

    if df.empty:
        return nodata_graph

    # Create figure
    fig = hu.create_heatmap_figure(df, color_label="Contributors")

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start:.2f}s")
    return fig


def process_data(
    df_file: pd.DataFrame,
    df_actions: pd.DataFrame,
    df_file_cntrbs: pd.DataFrame,
    directory: str,
    bot_switch: bool,
) -> pd.DataFrame:
    """
    Process data for contributor file heatmap.

    Steps:
    1. Clean file data and join with contributor data
    2. Aggregate contributors by directory
    3. Map contributors to their last activity dates
    4. Create time-based matrix for heatmap
    """
    try:
        # Step 1: Prepare file dataframe
        df_file = hu.prepare_file_df(df_file)

        if df_file.empty:
            return pd.DataFrame()

        # Clean contributor data
        df_file_cntrbs = df_file_cntrbs.copy()
        if "repo_id" in df_file_cntrbs.columns:
            df_file_cntrbs = df_file_cntrbs.drop(columns=["repo_id"])
        if "reviewer_ids" in df_file_cntrbs.columns:
            df_file_cntrbs = df_file_cntrbs.drop(columns=["reviewer_ids"])

        # Merge file data with contributor data
        df_file = hu.safe_merge(df_file, df_file_cntrbs, on="file_path", how="left")

        if df_file.empty:
            return pd.DataFrame()

        # Fill NaN with empty lists and filter bots
        df_file = df_file.copy()
        df_file["cntrb_ids"] = df_file["cntrb_ids"].apply(lambda x: x if isinstance(x, list) else [])

        if bot_switch:
            bots_list = getattr(app, "bots_list", [])
            df_file["cntrb_ids"] = df_file["cntrb_ids"].apply(lambda ids: [x for x in ids if x not in bots_list])

        # Step 2: Aggregate by directory
        df_dir = aggregate_cntrbs_by_directory(df_file, directory)

        if df_dir.empty:
            return pd.DataFrame()

        # Step 3: Map contributors to last activity
        df_dir = map_cntrbs_to_last_activity(df_dir, df_actions)

        if df_dir.empty:
            return pd.DataFrame()

        # Step 4: Create time matrix
        result = create_time_matrix(df_dir, df_actions)

        return result

    except Exception as e:
        logging.error(f"Error processing data: {e}")
        return pd.DataFrame()


def aggregate_cntrbs_by_directory(df_file: pd.DataFrame, directory: str) -> pd.DataFrame:
    """Aggregate contributors by directory level."""
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

        # Check if any contributors exist
        if "cntrb_ids" not in df_filtered.columns:
            return pd.DataFrame()

        # Count files with no contributors
        num_empty = df_filtered["cntrb_ids"].apply(len).eq(0).sum()
        if num_empty == len(df_filtered):
            return pd.DataFrame()

        # Get group column
        group_column = level + 1

        if group_column not in df_filtered.columns:
            return pd.DataFrame()

        # Group and aggregate
        result = (
            df_filtered.groupby(group_column)["cntrb_ids"]
            .sum()
            .reset_index()
            .rename(columns={group_column: "directory_value"})
        )

        # Convert to sets to remove duplicates
        result["cntrb_ids"] = result["cntrb_ids"].apply(lambda x: set(x) if isinstance(x, list) else set())

        return result

    except Exception as e:
        logging.error(f"Error aggregating contributors by directory: {e}")
        return pd.DataFrame()


def map_cntrbs_to_last_activity(df_dir: pd.DataFrame, df_actions: pd.DataFrame) -> pd.DataFrame:
    """Map contributors to their last activity dates."""
    try:
        # Prepare actions dataframe
        df_actions = df_actions.copy()
        df_actions["created_at"] = pd.to_datetime(df_actions["created_at"], utc=True)

        # Get most recent activity per contributor
        df_last = df_actions.sort_values(by="created_at", ascending=False).drop_duplicates(
            subset="cntrb_id", keep="first"
        )

        # Create contributor to last activity mapping
        last_activity = df_last.set_index("cntrb_id")["created_at"].to_dict()

        # Map contributors to dates
        df_dir = df_dir.copy()
        df_dir["dates"] = df_dir["cntrb_ids"].apply(
            lambda ids: [last_activity.get(str(x)) for x in ids if str(x) in last_activity]
        )

        # Explode dates
        df_dir = df_dir.explode("dates")

        return df_dir

    except Exception as e:
        logging.error(f"Error mapping contributors to last activity: {e}")
        return pd.DataFrame()


def create_time_matrix(df_dir: pd.DataFrame, df_actions: pd.DataFrame) -> pd.DataFrame:
    """Create time-based matrix for heatmap."""
    try:
        # Separate rows with and without dates
        no_contribs = df_dir[df_dir["dates"].isna()]["directory_value"].tolist()
        df_with_dates = df_dir[df_dir["dates"].notna()]

        if df_with_dates.empty:
            return pd.DataFrame()

        # Get date range from PR opened actions
        df_actions = df_actions.copy()
        df_actions["created_at"] = pd.to_datetime(df_actions["created_at"], utc=True)

        pr_opened = df_actions[df_actions["Action"] == "PR Opened"]
        if pr_opened.empty:
            min_date = df_actions["created_at"].min()
        else:
            min_date = pr_opened["created_at"].min()

        max_date = df_actions["created_at"].max()

        if pd.isna(min_date) or pd.isna(max_date):
            return pd.DataFrame()

        # Create filler dates
        df_fill = hu.create_time_range_df(min_date, max_date, "dates")

        # Combine with data
        df_combined = pd.concat([df_with_dates[["directory_value", "dates"]], df_fill], axis=0)
        df_combined["directory_value"] = df_combined["directory_value"].astype(str)

        # Group by month and count
        result = df_combined.groupby(pd.Grouper(key="dates", freq="1M"))["directory_value"].value_counts().unstack(0)

        # Remove "nan" row if exists
        if "nan" in result.index:
            result = result.drop("nan")

        # Add back files with no contributors
        for file in no_contribs:
            if file not in result.index:
                result.loc[str(file)] = None

        return result

    except Exception as e:
        logging.error(f"Error creating time matrix: {e}")
        return pd.DataFrame()
