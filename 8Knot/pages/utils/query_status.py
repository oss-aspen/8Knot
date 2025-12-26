"""
Query status checking utilities for visualizations.

Provides functions to check if specific queries are ready without
waiting for all global queries to complete. This enables lazy loading
where visualizations render as soon as their data is available.
"""

import time
import logging
from celery.result import AsyncResult
import cache_manager.cache_facade as cf
from pages.index.query_constants import VISUALIZATION_QUERY_TIMEOUT, VISUALIZATION_POLL_INTERVAL


def wait_for_query_data(
    query_func, repolist, timeout=VISUALIZATION_QUERY_TIMEOUT, poll_interval=VISUALIZATION_POLL_INTERVAL
):
    """
    Wait for a specific query's data to become available in cache.

    This function polls both the cache and the job status to determine
    when data is ready, enabling visualizations to start as soon as
    their specific query completes, rather than waiting for all queries.

    Args:
        query_func: The query function (e.g., repo_languages_query)
        repolist: List of repo IDs
        timeout: Maximum seconds to wait (default: VISUALIZATION_QUERY_TIMEOUT)
        poll_interval: Seconds between checks (default: VISUALIZATION_POLL_INTERVAL)

    Returns:
        bool: True if data is ready, False if timeout
    """
    query_name = query_func.__name__
    viz_id = f"wait_for_{query_name}"
    start_time = time.time()

    logging.info(f"{viz_id} - Waiting for {query_name} data to become available")

    while True:
        # Check if we've exceeded timeout
        elapsed = time.time() - start_time
        if elapsed > timeout:
            logging.warning(f"{viz_id} - Timeout after {timeout}s waiting for {query_name}")
            return False

        # Check if data is in cache (get list of repos NOT yet cached)
        repos_not_cached = cf.get_uncached(func_name=query_name, repolist=repolist)

        # If all repos are cached, data is ready
        all_repos_cached = len(repos_not_cached) == 0
        if all_repos_cached:
            logging.info(f"{viz_id} - {query_name} data is ready (waited {elapsed:.2f}s)")
            return True

        # Log progress every 5 seconds
        if int(elapsed) % 5 == 0 and elapsed > 0:
            logging.debug(f"{viz_id} - Still waiting for {query_name} ({len(repos_not_cached)} repos not cached)")

        time.sleep(poll_interval)


def is_query_ready(query_func, repolist):
    """
    Check if a query's data is already available in cache (non-blocking).

    Args:
        query_func: The query function (e.g., repo_languages_query)
        repolist: List of repo IDs

    Returns:
        bool: True if data is available, False otherwise
    """
    query_name = query_func.__name__
    repos_not_cached = cf.get_uncached(func_name=query_name, repolist=repolist)
    all_repos_cached = len(repos_not_cached) == 0
    return all_repos_cached


def get_query_status(query_func, repolist):
    """
    Get detailed status of a query's data availability.

    Args:
        query_func: The query function
        repolist: List of repo IDs

    Returns:
        dict: Status information with keys:
            - ready: bool - Whether all data is cached
            - cached_count: int - Number of repos with cached data
            - total_count: int - Total number of repos requested
            - missing_repos: list - Repo IDs not yet cached
    """
    query_name = query_func.__name__
    repos_not_cached = cf.get_uncached(func_name=query_name, repolist=repolist)

    cached_count = len(repolist) - len(repos_not_cached)
    all_repos_cached = len(repos_not_cached) == 0

    return {
        "ready": all_repos_cached,
        "cached_count": cached_count,
        "total_count": len(repolist),
        "missing_repos": repos_not_cached,
        "query_name": query_name,
    }
