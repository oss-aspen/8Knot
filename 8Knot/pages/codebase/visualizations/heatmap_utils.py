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
from app import augur
import cache_manager.cache_facade as cf
from queries.repo_files_query import repo_files_query as rfq


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
