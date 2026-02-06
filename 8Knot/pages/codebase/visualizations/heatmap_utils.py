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


# Default timeout for cache waiting (in seconds)
CACHE_TIMEOUT = 300


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
        logging.warning(f"HEATMAP - WAITING ON {query_func_name} DATA")
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
        Sorted list of directories with "Top Level Directory" as first option
    """
    if df.empty or "file_path" not in df.columns:
        return ["Top Level Directory"]

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
        directories.insert(0, "Top Level Directory")

        return directories

    except Exception as e:
        logging.error(f"Error extracting directories: {e}")
        return ["Top Level Directory"]


def aggregate_by_directory(df: pd.DataFrame, directory: str, value_column: str, agg_func: str = "sum") -> pd.DataFrame:
    """
    Group data by directory level and aggregate values.

    Args:
        df: DataFrame with file path data split into columns
        directory: Selected directory (or "Top Level Directory")
        value_column: Column name to aggregate
        agg_func: Aggregation function ("sum", "count", etc.)

    Returns:
        DataFrame with directory_value and aggregated values
    """
    if df.empty:
        return pd.DataFrame()

    try:
        # Determine directory level
        level = directory.count("/")
        if directory == "Top Level Directory":
            level = -1
            directory = ""

        # Filter to files in selected directory
        df_filtered = df[df["file_path"].str.startswith(directory, na=False)]

        if df_filtered.empty:
            return pd.DataFrame()

        # Get one level up from the directory level
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

    Cleans file paths, drops unnecessary columns, and splits paths.

    Args:
        df: Raw file dataframe from repo_files_query

    Returns:
        Cleaned DataFrame ready for further processing
    """
    if df.empty:
        return df

    try:
        # Clean file paths (also renames 'id' to 'repo_id')
        df = clean_file_path(df)

        # Keep only most recent analysis date
        if "rl_analysis_date" in df.columns:
            df = df[df["rl_analysis_date"] == df["rl_analysis_date"].max()]

        # Reset index and drop unnecessary columns
        df = df.reset_index(drop=True)

        columns_to_drop = ["repo_name", "repo_path", "rl_analysis_date", "repo_id", "id"]
        columns_to_drop = [c for c in columns_to_drop if c in df.columns]
        df = df.drop(columns=columns_to_drop, errors="ignore")

        # Split file path by directory
        if "file_path" in df.columns:
            path_split = df["file_path"].str.split("/", expand=True)
            df = df.join(path_split)

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
