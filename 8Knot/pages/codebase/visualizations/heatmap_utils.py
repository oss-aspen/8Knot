"""
Shared utilities for heatmap visualizations.

This module contains common functions used across all heatmap visualizations
(cntrb_file_heatmap, contribution_file_heatmap, reviewer_file_heatmap) to
reduce code duplication and improve maintainability.

Following DRY (Don't Repeat Yourself) principle.
"""

import logging
import time
import pandas as pd
import plotly.express as px
from app import augur
import cache_manager.cache_facade as cf
from queries.repo_files_query import repo_files_query as rfq
from queries.contributors_query import contributors_query as cnq
from queries.cntrb_per_file_query import cntrb_per_file_query as cpfq
from pages.utils.job_utils import nodata_graph
import pages.utils.preprocessing_utils as preproc_u
import app


def create_repo_dropdown(repo_ids, viz_id):
    """
    Create dropdown data for repository selection.

    Args:
        repo_ids: List of repository IDs
        viz_id: Visualization ID for logging

    Returns:
        Tuple of (dropdown_data, default_value)
        - dropdown_data: List of dicts with "value" and "label" keys
        - default_value: First valid repo_id or None if no valid repos
    """
    if not repo_ids or len(repo_ids) == 0:
        logging.warning(f"{viz_id} - NO REPO_IDS PROVIDED")
        return [], None

    data_array = []
    for repo_id in repo_ids:
        try:
            entry = {"value": repo_id, "label": augur.repo_id_to_git(repo_id)}
            data_array.append(entry)
        except Exception as e:
            logging.error(f"{viz_id} - ERROR getting git URL for repo_id {repo_id}: {e}")
            continue

    if not data_array:
        logging.warning(f"{viz_id} - NO VALID REPO_IDS")
        return [], None

    # Return first valid repo_id, ensuring we don't hit IndexError
    return data_array, data_array[0]["value"] if data_array else None


def create_directory_dropdown(repo_id, viz_id, max_wait_time=180):
    """
    Create dropdown data for directory selection with timeout protection.

    This function waits for repository file data to be cached, then processes
    the file paths to extract directory structure.

    Args:
        repo_id: Repository ID
        viz_id: Visualization ID for logging
        max_wait_time: Maximum seconds to wait for data (default: 180)

    Returns:
        Tuple of (directories_list, default_value)
        - directories_list: Sorted list of directory paths
        - default_value: "Top Level Directory"
    """
    # Validate repo_id
    if repo_id is None:
        logging.warning(f"{viz_id} DROPDOWN - NO REPO_ID PROVIDED")
        return ["Top Level Directory"], "Top Level Directory"

    # Add timeout protection to prevent SoftTimeLimitExceeded
    start_time = time.perf_counter()

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=rfq.__name__, repolist=[repo_id]):
        # Check for timeout
        elapsed = time.perf_counter() - start_time
        if elapsed > max_wait_time:
            logging.error(f"{viz_id} DROPDOWN - TIMEOUT after {elapsed:.1f}s waiting for data. Repo ID: {repo_id}")
            return ["Top Level Directory"], "Top Level Directory"

        logging.info(f"DIRECTORY DROPDOWN - WAITING ON DATA TO BECOME AVAILABLE (elapsed: {elapsed:.1f}s)")
        time.sleep(0.5)

    logging.info(f"DIRECTORY DROPDOWN - RETRIEVING FROM CACHE")
    df = cf.retrieve_from_cache(
        tablename=rfq.__name__,
        repolist=[repo_id],
    )

    logging.info(f"DIRECTORY DROPDOWN - CACHE READ")

    # test if there is data
    if df.empty:
        logging.warning(f"{viz_id} DROPDOWN- NO DATA AVAILABLE")
        return ["Top Level Directory"], "Top Level Directory"

    # strings to hold the values for each column (always the same for every row of this query)
    repo_name = df["repo_name"].iloc[0]
    repo_path = df["repo_path"].iloc[0]
    repo_id_str = str(df["repo_id"].iloc[0])

    # pattern found in each file path, used to slice to get only the root file path
    path_slice = repo_id_str + "-" + repo_path + "/" + repo_name + "/"
    # Use .str.get(1) instead of .str[1] to handle missing path_slice gracefully
    df["file_path"] = df["file_path"].str.rsplit(path_slice, n=1).str.get(1)
    # Drop rows where path_slice was not found (file_path is NaN)
    df = df.dropna(subset=["file_path"])

    # drop columns not in the most recent collection
    df = df[df["rl_analysis_date"] == df["rl_analysis_date"].max()]

    # drop unneccessary columns not needed after preprocessing steps
    df = df.reset_index()
    df = df.drop(
        ["index", "repo_id", "repo_name", "repo_path", "rl_analysis_date"],
        axis=1,
    )

    # split file path by directory
    df = df.join(df["file_path"].str.split("/", expand=True))

    # take all of the files, split on the last instance of a / to get directories and top level files
    directories = df["file_path"].str.rsplit("/", n=1).str[0].tolist()
    # applies another rsplit to make sure directories that only have folders are included
    folder_only_directories = [x.rsplit("/", 1)[0] for x in directories]
    directories = list(set(directories + folder_only_directories))

    # get all of the file names to filter out of the directory set
    # Column index 1 represents the first directory level after splitting
    first_dir_level = df.iloc[:, 1] if len(df.columns) > 1 else pd.Series()
    top_level_files = df["file_name"][first_dir_level.isnull()].tolist() if len(first_dir_level) > 0 else []
    directories = [f for f in directories if f not in top_level_files]

    # sort alphabetically
    directories = sorted(directories)

    # add top level directory to the list of directories
    directories.insert(0, "Top Level Directory")

    return directories, "Top Level Directory"


# ===============================================================================
# Shared functions for activity-based heatmaps (contributor/reviewer)
# These functions eliminate duplication between cntrb_file_heatmap.py
# and reviewer_file_heatmap.py by providing parameterized implementations
# ===============================================================================


def get_activity_heatmap_data(searchbar_repos, repo, viz_id):
    """
    Retrieve cached data for activity-based heatmaps.
    Shared by contributor and reviewer heatmaps.

    Args:
        searchbar_repos: List of repository IDs from searchbar
        repo: List with single repository ID
        viz_id: Visualization ID for logging

    Returns:
        Tuple of (df_file, df_actions, df_file_cntbs)
    """
    while cf.get_uncached(func_name=rfq.__name__, repolist=repo):
        logging.warning(f"{viz_id} - WAITING ON DATA")
        time.sleep(0.5)

    while cf.get_uncached(func_name=cnq.__name__, repolist=searchbar_repos):
        logging.warning(f"{viz_id} - WAITING ON DATA")
        time.sleep(0.5)

    while cf.get_uncached(func_name=cpfq.__name__, repolist=repo):
        logging.warning(f"{viz_id} - WAITING ON DATA")
        time.sleep(0.5)

    df_file = cf.retrieve_from_cache(tablename=rfq.__name__, repolist=repo)
    df_actions = cf.retrieve_from_cache(tablename=cnq.__name__, repolist=searchbar_repos)
    df_file_cntrbs = cf.retrieve_from_cache(tablename=cpfq.__name__, repolist=repo)

    df_actions = preproc_u.contributors_df_action_naming(df_actions)
    df_file_cntrbs = preproc_u.cntrb_per_file(df_file_cntrbs)

    return df_file, df_actions, df_file_cntrbs


def process_activity_heatmap(df_file, df_actions, df_file_cntbs, directory, bot_switch, id_column):
    """
    Process data for activity heatmaps.
    Shared by contributor and reviewer heatmaps.

    Args:
        df_file: DataFrame with file data
        df_actions: DataFrame with contributor activity
        df_file_cntbs: DataFrame with IDs per file
        directory: Selected directory
        bot_switch: Boolean for bot filtering
        id_column: 'cntrb_ids' or 'reviewer_ids'

    Returns:
        DataFrame with files as rows, months as columns
    """
    df_file = prepare_file_data(df_file, df_file_cntbs, bot_switch, id_column)
    df_dynamic = aggregate_by_directory_level(directory, df_file, id_column)

    if df_dynamic.empty:
        return df_dynamic

    df_dynamic = map_to_last_activity_date(df_actions, df_dynamic, id_column)
    return create_monthly_activity_matrix(df_dynamic, df_actions)


def prepare_file_data(df_file, df_file_cntbs, bot_switch, id_column):
    """Clean and merge file data with contributor/reviewer IDs."""
    repo_name = df_file["repo_name"].iloc[0] if df_file["repo_name"].iloc[0] else ""
    repo_path = df_file["repo_path"].iloc[0] if df_file["repo_path"].iloc[0] else ""
    repo_id = str(df_file["repo_id"].iloc[0])

    path_slice = f"{repo_id}-{repo_path}/{repo_name}/"
    original = df_file["file_path"].copy()
    df_file["file_path"] = df_file["file_path"].str.rsplit(path_slice, n=1).str[1]
    df_file["file_path"] = df_file["file_path"].fillna(original).astype(str)

    df_file = df_file.reset_index(drop=True)
    df_file = df_file.drop(["repo_name", "repo_path", "rl_analysis_date", "repo_id"], axis=1)
    df_file = df_file.join(df_file["file_path"].str.split("/", expand=True))

    drop_col = "cntrb_ids" if id_column == "reviewer_ids" else "reviewer_ids"
    df_file_cntbs = df_file_cntbs.drop(["repo_id", drop_col], axis=1)

    df_file = pd.merge(df_file, df_file_cntbs, on="file_path", how="left")
    df_file[id_column] = df_file[id_column].fillna("")

    if bot_switch:
        df_file[id_column] = df_file.apply(lambda row: [x for x in row[id_column] if x not in app.bots_list], axis=1)
    else:
        df_file[id_column] = df_file.apply(lambda row: [x for x in row[id_column]], axis=1)

    return df_file


def aggregate_by_directory_level(directory, df_file, id_column):
    """Aggregate IDs by directory level."""
    if directory is None or directory == "Top Level Directory":
        level, directory = -1, ""
    else:
        level = directory.count("/")

    df_dir = df_file[df_file["file_path"].str.startswith(directory)]
    num_empty = df_dir[df_dir[id_column].str.len() == 0].shape[0]

    if num_empty == df_dir.shape[0]:
        return pd.DataFrame()

    group_col = level + 1
    df_dir = df_dir.groupby(group_col)[id_column].sum().reset_index().rename(columns={group_col: "directory_value"})

    df_dir[id_column] = df_dir.apply(lambda row: set(row[id_column]), axis=1)
    return df_dir


def map_to_last_activity_date(df_actions, df_dir, id_column):
    """Map IDs to their last activity dates."""
    df_actions["created_at"] = pd.to_datetime(df_actions["created_at"], utc=True)
    df_actions = df_actions.sort_values(by="created_at", ascending=False)
    df_actions = df_actions.drop_duplicates(subset="cntrb_id", keep="first")

    df_actions = df_actions.reset_index(drop=True)
    df_actions = df_actions.drop(["repo_id", "repo_name", "login", "Action", "rank"], axis=1)

    last_activity = df_actions.set_index("cntrb_id")["created_at"].to_dict()
    df_dir["dates"] = df_dir.apply(lambda row: [last_activity[x] for x in row[id_column]], axis=1)

    return df_dir.explode("dates")


def create_monthly_activity_matrix(df_dir, df_actions):
    """Transform data to monthly activity counts."""
    no_contribs = df_dir["directory_value"][df_dir.dates.isnull()].tolist()
    df_dir = df_dir[~df_dir.dates.isnull()]

    min_date = df_actions[df_actions["Action"] == "PR Opened"].created_at.min()
    max_date = df_actions.created_at.max()
    dates = pd.date_range(start=min_date, end=max_date, freq="M", inclusive="both")
    df_fill = dates.to_frame(index=False, name="dates")

    final = pd.concat([df_dir, df_fill], axis=0)
    final["directory_value"] = final["directory_value"].astype(str)
    final = final.groupby(pd.Grouper(key="dates", freq="1M"))["directory_value"].value_counts().unstack(0)

    if "nan" in final.index:
        final = final.drop("nan")

    for f in no_contribs:
        final.loc[f] = None

    return final


def create_activity_heatmap_figure(df):
    """Create plotly heatmap figure for activity visualizations."""
    fig = px.imshow(
        df,
        labels=dict(x="Time", y="Directory Entries", color="Contributors"),
        color_continuous_scale=px.colors.sequential.deep,
    )

    fig["layout"]["yaxis"]["tickmode"] = "linear"
    fig["layout"]["height"] = 700
    fig["layout"]["coloraxis_colorbar_x"] = -0.15
    fig["layout"]["yaxis"]["side"] = "right"

    fig.for_each_trace(
        lambda trace: trace.update(
            customdata=df.map(lambda x: "No data" if pd.isna(x) else x),
            hovertemplate="<b>%{y}</b><br>Time: %{x}<br>Contributors: %{customdata}<extra></extra>",
        )
    )

    return fig
