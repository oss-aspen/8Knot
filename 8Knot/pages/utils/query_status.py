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


def wait_for_query_data(query_func, repolist, timeout=600, poll_interval=0.5):
    """
    Wait for a specific query's data to become available in cache.

    This function polls both the cache and the job status to determine
    when data is ready, enabling visualizations to start as soon as
    their specific query completes, rather than waiting for all queries.

    Args:
        query_func: The query function (e.g., repo_languages_query)
        repolist: List of repo IDs
        timeout: Maximum seconds to wait (default: 600 = 10 minutes)
        poll_interval: Seconds between checks (default: 0.5)

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

        # Check if data is in cache
        not_cached = cf.get_uncached(func_name=query_name, repolist=repolist)

        if not not_cached:
            # Data is available in cache
            logging.info(f"{viz_id} - {query_name} data is ready (waited {elapsed:.2f}s)")
            return True

        # Log progress every 5 seconds
        if int(elapsed) % 5 == 0 and elapsed > 0:
            logging.debug(f"{viz_id} - Still waiting for {query_name} ({len(not_cached)} repos not cached)")

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
    not_cached = cf.get_uncached(func_name=query_name, repolist=repolist)
    return not not_cached


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
    not_cached = cf.get_uncached(func_name=query_name, repolist=repolist)

    cached_count = len(repolist) - len(not_cached)

    return {
        "ready": len(not_cached) == 0,
        "cached_count": cached_count,
        "total_count": len(repolist),
        "missing_repos": not_cached,
        "query_name": query_name,
    }
