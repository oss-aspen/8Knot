"""
Shared utilities for codebase heatmap visualizations.

This module provides common functions used across all three heatmap visualizations:
- Contribution File Heatmap
- Contributor File Heatmap
- Reviewer File Heatmap
"""

import logging
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import cache_manager.cache_facade as cf
from pages.utils.job_utils import nodata_graph
import app


# Constants
CACHE_TIMEOUT = 300  # Default timeout for cache waiting (in seconds)
TOP_LEVEL_DIRECTORY = "Top Level Directory"


def wait_for_cache(query_func_name: str, repolist: list, timeout: int = CACHE_TIMEOUT) -> bool:
    """
    Wait for cache data to become available with timeout.

    Args:
        query_func_name: Name of the query function (e.g., 'repo_files_query')
        repolist: List of repo IDs to check
        timeout: Maximum time to wait in seconds

    Returns:
        True if cache is ready, False if timeout exceeded
    """
    start_time = time.time()

    while not_cached := cf.get_uncached(func_name=query_func_name, repolist=repolist):
        if time.time() - start_time > timeout:
            logging.error(f"Cache timeout exceeded for {query_func_name}")
            return False
        logging.info(f"Waiting on {query_func_name} data for repos {repolist}")
        time.sleep(0.5)

    return True


def retrieve_cached_data(query_func_name: str, repolist: list) -> pd.DataFrame:
    """
    Retrieve data from cache with error handling.

    Args:
        query_func_name: Name of the query function
        repolist: List of repo IDs

    Returns:
        DataFrame with cached data, or empty DataFrame on error
    """
    try:
        df = cf.retrieve_from_cache(
            tablename=query_func_name,
            repolist=repolist,
        )
        return df if df is not None else pd.DataFrame()
    except Exception as e:
        logging.error(f"Error retrieving cache for {query_func_name}: {e}")
        return pd.DataFrame()


def clean_file_path(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize file paths by removing repo prefix.

    Handles null values for repo_name, repo_path, and repo_id safely.
    Note: repo_files_query returns 'id' instead of 'repo_id'.

    Args:
        df: DataFrame with file_path, repo_name, repo_path, and id/repo_id columns

    Returns:
        DataFrame with cleaned file_path column
    """
    if df.empty:
        return df

    # Safe access to first row values
    try:
        repo_name = df["repo_name"].iloc[0]
        repo_path = df["repo_path"].iloc[0]

        # Handle both 'id' and 'repo_id' column names
        if "id" in df.columns:
            repo_id = df["id"].iloc[0]
            # Rename 'id' to 'repo_id' for consistency
            df = df.rename(columns={"id": "repo_id"})
        elif "repo_id" in df.columns:
            repo_id = df["repo_id"].iloc[0]
        else:
            logging.warning("No repo_id or id column found")
            return df

        # Check for None or empty string values
        if not repo_name or not repo_path or repo_id is None:
            logging.warning(
                f"Null or empty values in repo metadata: repo_name='{repo_name}', repo_path='{repo_path}', repo_id={repo_id}"
            )
            return df

        repo_id_str = str(repo_id)

        # Pattern found in each file path, used to slice to get only the root file path
        path_slice = f"{repo_id_str}-{repo_path}/{repo_name}/"

        # Handle None in file_path column
        df = df.copy()
        df["file_path"] = df["file_path"].fillna("")
        df["file_path"] = df["file_path"].str.rsplit(path_slice, n=1).str[-1]

    except (IndexError, KeyError) as e:
        logging.error(f"Error cleaning file paths: {e}")

    return df


def get_directories(df: pd.DataFrame) -> list:
    """
    Extract sorted list of directories from file dataframe.

    Args:
        df: DataFrame with file_path and file_name columns

    Returns:
        Sorted list of directories with TOP_LEVEL_DIRECTORY as first option
    """
    if df.empty or "file_path" not in df.columns:
        return [TOP_LEVEL_DIRECTORY]

    try:
        # Split file path by directory to identify hierarchy
        df = df.copy()

        # Only split if not already split (check if numeric columns exist)
        if 0 not in df.columns:
            df = df.join(df["file_path"].str.split("/", expand=True))

        # Get directories from file paths
        directories = df["file_path"].str.rsplit("/", n=1).str[0].tolist()

        # Add parent directories
        folder_only_directories = []
        for d in directories:
            if d and "/" in d:
                folder_only_directories.append(d.rsplit("/", 1)[0])
        directories = list(set(directories + folder_only_directories))

        # Filter out top-level files (not directories)
        if 1 in df.columns:
            top_level_files = df["file_name"][df[1].isnull()].tolist()
            directories = [d for d in directories if d and d not in top_level_files]

        # Sort and add top level option
        directories = sorted([d for d in directories if d])
        directories.insert(0, TOP_LEVEL_DIRECTORY)

        return directories

    except Exception as e:
        logging.error(f"Error extracting directories: {e}")
        return [TOP_LEVEL_DIRECTORY]


def aggregate_by_directory(df: pd.DataFrame, directory: str, value_column: str, agg_func: str = "sum") -> pd.DataFrame:
    """
    Group data by directory level and aggregate values.

    Args:
        df: DataFrame with file path data split into columns
        directory: Selected directory (or TOP_LEVEL_DIRECTORY)
        value_column: Column name to aggregate
        agg_func: Aggregation function ("sum", "count", etc.)

    Returns:
        DataFrame with directory_value and aggregated values
    """
    if df.empty:
        return pd.DataFrame()

    try:
        # Determine directory level (number of slashes = depth)
        # Top level = -1, first subdirectory = 0, etc.
        level = directory.count("/")
        if directory == TOP_LEVEL_DIRECTORY:
            level = -1
            directory = ""

        # Filter to files in selected directory
        df_filtered = df[df["file_path"].str.startswith(directory, na=False)]

        if df_filtered.empty:
            return pd.DataFrame()

        # Group column is one level deeper than current directory level
        group_column = level + 1

        # Check if group column exists
        if group_column not in df_filtered.columns:
            return pd.DataFrame()

        # Group by directory level
        if agg_func == "sum":
            result = (
                df_filtered.groupby(group_column)[value_column]
                .sum()
                .reset_index()
                .rename(columns={group_column: "directory_value"})
            )
        elif agg_func == "count":
            result = (
                df_filtered.groupby(group_column)[value_column]
                .count()
                .reset_index()
                .rename(columns={group_column: "directory_value"})
            )
        else:
            result = (
                df_filtered.groupby(group_column)[value_column]
                .apply(list)
                .reset_index()
                .rename(columns={group_column: "directory_value"})
            )

        return result

    except Exception as e:
        logging.error(f"Error aggregating by directory: {e}")
        return pd.DataFrame()


def create_heatmap_figure(
    df: pd.DataFrame,
    x_label: str = "Time",
    y_label: str = "Directory Entries",
    color_label: str = "Count",
    height: int = 700,
) -> go.Figure:
    """
    Create consistent heatmap figure with standard styling.

    Args:
        df: DataFrame in matrix format (index=y-axis, columns=x-axis)
        x_label: Label for x-axis
        y_label: Label for y-axis
        color_label: Label for color scale
        height: Figure height in pixels

    Returns:
        Plotly Figure object
    """
    if df.empty:
        return nodata_graph

    try:
        fig = px.imshow(
            df,
            labels=dict(x=x_label, y=y_label, color=color_label),
            color_continuous_scale=px.colors.sequential.deep,
        )

        fig.update_layout(
            yaxis=dict(
                tickmode="linear",
                side="right",
            ),
            height=height,
            coloraxis_colorbar_x=-0.15,
        )

        return fig

    except Exception as e:
        logging.error(f"Error creating heatmap figure: {e}")
        return nodata_graph


def prepare_file_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Common preprocessing for file dataframes.

    Orchestrates cleaning, filtering, and path splitting using focused helper functions.
    Improved for SRP compliance.

    Args:
        df: Raw file dataframe from repo_files_query

    Returns:
        Cleaned DataFrame ready for further processing
    """
    if df.empty:
        return df

    try:
        # Step 1: Clean file paths (also renames 'id' to 'repo_id')
        df = clean_file_path(df)

        # Step 2: Keep only most recent analysis date
        df = filter_by_latest_analysis(df)

        # Step 3: Reset index
        df = df.reset_index(drop=True)

        # Step 4: Drop unnecessary metadata columns
        df = drop_metadata_columns(df)

        # Step 5: Split file path by directory hierarchy
        df = split_file_paths(df)

        return df

    except Exception as e:
        logging.error(f"Error preparing file dataframe: {e}")
        return pd.DataFrame()


def create_time_range_df(min_date, max_date, date_column: str = "dates") -> pd.DataFrame:
    """
    Create a DataFrame with monthly date range for heatmap column filling.

    This ensures all months are represented in the heatmap even if no data exists.

    Args:
        min_date: Start date
        max_date: End date
        date_column: Name for the date column

    Returns:
        DataFrame with monthly dates
    """
    try:
        dates = pd.date_range(start=min_date, end=max_date, freq="M", inclusive="both")
        return dates.to_frame(index=False, name=date_column)
    except Exception as e:
        logging.error(f"Error creating time range: {e}")
        return pd.DataFrame()


def safe_merge(left: pd.DataFrame, right: pd.DataFrame, on: str, how: str = "left") -> pd.DataFrame:
    """
    Safely merge two DataFrames with error handling.

    Args:
        left: Left DataFrame
        right: Right DataFrame
        on: Column to merge on
        how: Type of merge

    Returns:
        Merged DataFrame or empty DataFrame on error
    """
    try:
        if left.empty or right.empty:
            return left

        return pd.merge(left, right, on=on, how=how)

    except Exception as e:
        logging.error(f"Error merging dataframes: {e}")
        return pd.DataFrame()


# ============================================================================
# NEW UTILITY FUNCTIONS FOR DRY AND SRP IMPROVEMENTS
# ============================================================================


def filter_bots_from_ids(id_list: list, bot_switch: bool) -> list:
    """
    Filter bot IDs from a list of contributor/reviewer IDs.

    Args:
        id_list: List of contributor or reviewer IDs
        bot_switch: Whether to filter bots (True = filter out bots)

    Returns:
        Filtered list with bots removed if bot_switch is True
    """
    if not bot_switch:
        return id_list

    if not isinstance(id_list, list):
        return []

    bots_list = getattr(app, "bots_list", [])
    return [x for x in id_list if x not in bots_list]


def build_repo_dropdown_data(repo_ids: list, rfq_func) -> tuple[list, int]:
    """
    Build repository dropdown data with validation.

    Finds first repo with valid (non-empty) metadata and sets it as default.

    Args:
        repo_ids: List of repository IDs
        rfq_func: Reference to repo_files_query function for __name__ access

    Returns:
        Tuple of (data_array, default_repo_id)
    """
    from app import augur

    if not repo_ids:
        return [], None

    data_array = []
    for repo_id in repo_ids:
        try:
            label = augur.repo_id_to_git(repo_id)
            data_array.append({"value": repo_id, "label": label})
        except Exception as e:
            logging.debug(f"Error getting repo label for {repo_id}: {e}")
            data_array.append({"value": repo_id, "label": str(repo_id)})

    # Find first repo with valid metadata (non-empty repo_name and repo_path)
    default_repo = None
    for repo_id in repo_ids:
        df = retrieve_cached_data(rfq_func.__name__, [repo_id])
        if not df.empty:
            repo_name = df["repo_name"].iloc[0] if "repo_name" in df.columns else None
            repo_path = df["repo_path"].iloc[0] if "repo_path" in df.columns else None
            if repo_name and repo_path:  # Skip empty strings and None
                default_repo = repo_id
                break

    if default_repo is None:
        default_repo = repo_ids[0] if repo_ids else None

    return data_array, default_repo


def aggregate_ids_by_directory(df_file: pd.DataFrame, directory: str, id_column: str) -> pd.DataFrame:
    """
    Aggregate contributor/reviewer/PR IDs by directory level.

    This is a specialized version of aggregate_by_directory for ID lists.

    Args:
        df_file: DataFrame with file paths split into columns
        directory: Selected directory
        id_column: Column name containing ID lists (e.g., 'cntrb_ids', 'reviewer_ids', 'pull_request_id')

    Returns:
        DataFrame with directory_value and aggregated ID sets
    """
    try:
        # Determine directory level
        level = directory.count("/")
        if directory == TOP_LEVEL_DIRECTORY:
            level = -1
            directory = ""

        # Filter to files in selected directory
        df_filtered = df_file[df_file["file_path"].str.startswith(directory, na=False)]

        if df_filtered.empty:
            return pd.DataFrame()

        # Check if ID column exists
        if id_column not in df_filtered.columns:
            return pd.DataFrame()

        # Count items with no IDs
        num_empty = df_filtered[id_column].apply(lambda x: len(x) if isinstance(x, list) else 0).eq(0).sum()
        if num_empty == len(df_filtered):
            return pd.DataFrame()

        # Get group column (one level deeper than current directory)
        group_column = level + 1

        if group_column not in df_filtered.columns:
            return pd.DataFrame()

        # Group and aggregate IDs
        result = (
            df_filtered.groupby(group_column)[id_column]
            .sum()  # Concatenate lists
            .reset_index()
            .rename(columns={group_column: "directory_value"})
        )

        # Convert to sets to remove duplicates
        result[id_column] = result[id_column].apply(lambda x: set(x) if isinstance(x, list) else set())

        # Filter out empty sets
        result = result[result[id_column].apply(len) > 0]

        return result

    except Exception as e:
        logging.error(f"Error aggregating {id_column} by directory: {e}")
        return pd.DataFrame()


def map_ids_to_dates(
    df_dir: pd.DataFrame,
    df_source: pd.DataFrame,
    id_column: str,
    source_id_column: str,
    date_column: str,
    convert_to_string: bool = True,
) -> pd.DataFrame:
    """
    Map IDs to their associated dates.

    Generic function for mapping contributor/reviewer IDs to last activity dates,
    or PR IDs to created/merged dates.

    Args:
        df_dir: DataFrame with directory values and ID lists
        df_source: DataFrame with ID-to-date mappings
        id_column: Column name in df_dir containing ID lists
        source_id_column: Column name in df_source containing IDs
        date_column: Column name in df_source containing dates
        convert_to_string: Whether to convert IDs to strings for lookup (True for cntrb/reviewer, False for PRs)

    Returns:
        DataFrame with dates exploded (one row per date)
    """
    try:
        # Prepare source dataframe
        df_source = df_source.copy()
        df_source[date_column] = pd.to_datetime(df_source[date_column], utc=True)

        # Create ID to date mapping
        id_to_date = df_source.set_index(source_id_column)[date_column].to_dict()

        # Map IDs to dates (filter out NaN/NaT dates)
        df_dir = df_dir.copy()
        if convert_to_string:
            # For contributor/reviewer IDs (stored as strings)
            df_dir["dates"] = df_dir[id_column].apply(
                lambda ids: [
                    id_to_date.get(str(x)) for x in ids if str(x) in id_to_date and pd.notna(id_to_date.get(str(x)))
                ]
            )
        else:
            # For PR IDs (stored as integers)
            df_dir["dates"] = df_dir[id_column].apply(
                lambda ids: [id_to_date.get(x) for x in ids if x in id_to_date and pd.notna(id_to_date.get(x))]
            )

        # Explode dates (one row per date)
        df_dir = df_dir.explode("dates")

        return df_dir

    except Exception as e:
        logging.error(f"Error mapping {id_column} to dates: {e}")
        return pd.DataFrame()


def create_time_matrix(
    df_dir: pd.DataFrame,
    df_date_source: pd.DataFrame,
    date_column: str = "created_at",
    filter_action: str = None,
    items_without_dates: list = None,
) -> pd.DataFrame:
    """
    Create time-based matrix for heatmap visualization.

    Unified function for creating monthly time matrices from directory-date data.

    Args:
        df_dir: DataFrame with directory_value and dates columns
        df_date_source: DataFrame to determine date range
        date_column: Column name for dates in df_date_source
        filter_action: Optional action to filter for min date (e.g., "PR Opened")
        items_without_dates: Optional list of directory values with no dates

    Returns:
        DataFrame in matrix format (index=directories, columns=months)
    """
    try:
        # Separate rows with and without dates
        if items_without_dates is None:
            items_without_dates = df_dir[df_dir["dates"].isna()]["directory_value"].tolist()

        df_with_dates = df_dir[df_dir["dates"].notna()]

        if df_with_dates.empty:
            return pd.DataFrame()

        # Get date range from source data
        df_date_source = df_date_source.copy()
        df_date_source[date_column] = pd.to_datetime(df_date_source[date_column], utc=True)

        # Determine min date based on filter action if provided
        if filter_action:
            filtered = df_date_source[df_date_source["Action"] == filter_action]
            if not filtered.empty:
                min_date = filtered[date_column].min()
            else:
                min_date = df_date_source[date_column].min()
        else:
            min_date = df_date_source[date_column].min()

        max_date = df_date_source[date_column].max()

        if pd.isna(min_date) or pd.isna(max_date):
            return pd.DataFrame()

        # Create filler dates for complete month range
        df_fill = create_time_range_df(min_date, max_date, "dates")

        # Combine with data
        df_combined = pd.concat([df_with_dates[["directory_value", "dates"]], df_fill], axis=0)
        df_combined["directory_value"] = df_combined["directory_value"].astype(str)

        # Group by month and count occurrences per directory
        result = df_combined.groupby(pd.Grouper(key="dates", freq="1M"))["directory_value"].value_counts().unstack(0)

        # Remove "nan" row if exists
        if "nan" in result.index:
            result = result.drop("nan")

        # Add back items with no dates
        for item in items_without_dates:
            if item not in result.index:
                result.loc[str(item)] = None

        return result

    except Exception as e:
        logging.error(f"Error creating time matrix: {e}")
        return pd.DataFrame()


def split_file_paths(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split file paths into directory hierarchy columns.

    Separated from prepare_file_df for SRP compliance.

    Args:
        df: DataFrame with file_path column

    Returns:
        DataFrame with numeric columns (0, 1, 2, ...) for path components
    """
    if df.empty or "file_path" not in df.columns:
        return df

    try:
        path_split = df["file_path"].str.split("/", expand=True)
        df = df.join(path_split)
        return df
    except Exception as e:
        logging.error(f"Error splitting file paths: {e}")
        return df


def filter_by_latest_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter DataFrame to keep only rows from most recent analysis date.

    Separated from prepare_file_df for SRP compliance.

    Args:
        df: DataFrame with rl_analysis_date column

    Returns:
        Filtered DataFrame
    """
    if df.empty or "rl_analysis_date" not in df.columns:
        return df

    try:
        return df[df["rl_analysis_date"] == df["rl_analysis_date"].max()]
    except Exception as e:
        logging.error(f"Error filtering by analysis date: {e}")
        return df


def drop_metadata_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop metadata columns no longer needed after preprocessing.

    Separated from prepare_file_df for SRP compliance.

    Args:
        df: DataFrame with metadata columns

    Returns:
        DataFrame with metadata columns removed
    """
    if df.empty:
        return df

    try:
        columns_to_drop = ["repo_name", "repo_path", "rl_analysis_date", "repo_id", "id"]
        columns_to_drop = [c for c in columns_to_drop if c in df.columns]
        return df.drop(columns=columns_to_drop, errors="ignore")
    except Exception as e:
        logging.error(f"Error dropping metadata columns: {e}")
        return df
