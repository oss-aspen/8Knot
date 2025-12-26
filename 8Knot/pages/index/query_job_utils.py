"""
Helper utilities for managing query jobs and async task polling.

These utilities follow SOLID principles:
- Single Responsibility: Each function has one clear purpose
- DRY: Eliminates code duplication across callback functions
- KISS: Simple, focused functions that are easy to test and maintain
"""

import time
import logging
from celery.result import AsyncResult
from .query_constants import (
    QUERY_STATUS_CACHED,
    PAGE_STATUS_READY,
    PAGE_STATUS_FAILED,
    PAGE_STATUS_TIMEOUT,
    GLOBAL_QUERY_POLL_INTERVAL,
    MAX_QUERY_WAIT_TIME,
    FAILURE_WAIT_INTERVAL,
)


def create_async_results_from_metadata(job_metadata, filter_query_names=None):
    """
    Create AsyncResult objects from job metadata, filtering out cached jobs.

    DRY principle: Centralizes the logic for converting job metadata to AsyncResult objects,
    eliminating duplication between wait_queries() and wait_current_page_queries().

    Args:
        job_metadata (dict): Dict mapping {query_name: job_id}
        filter_query_names (list, optional): List of query names to filter by.
                                             If None, uses all queries in metadata.

    Returns:
        tuple: (jobs, query_names) where:
            - jobs: List of AsyncResult objects for non-cached jobs
            - query_names: List of corresponding query names
    """
    jobs = []
    query_names = []

    # Determine which queries to process
    # Use explicit None check: empty list means "no queries", None means "all queries"
    queries_to_process = job_metadata.keys() if filter_query_names is None else filter_query_names

    for query_name in queries_to_process:
        if query_name in job_metadata:
            job_id = job_metadata[query_name]
            if job_id != QUERY_STATUS_CACHED:
                jobs.append(AsyncResult(job_id))
                query_names.append(query_name)

    return jobs, query_names


def check_all_jobs_complete(job_metadata):
    """
    Check if all jobs in metadata are complete (either cached or successful).

    Optimized to avoid creating unnecessary AsyncResult objects during early returns.

    Args:
        job_metadata (dict): Dict mapping {query_name: job_id}

    Returns:
        bool: True if all jobs are complete, False otherwise
    """
    for job_id in job_metadata.values():
        # Skip cached jobs (already complete)
        if job_id == QUERY_STATUS_CACHED:
            continue

        # Check if job is successful
        result = AsyncResult(job_id)
        if not result.successful():
            return False

    return True


def wait_for_job_completion(
    jobs,
    query_names,
    poll_interval=GLOBAL_QUERY_POLL_INTERVAL,
    max_wait_time=MAX_QUERY_WAIT_TIME,
    context="",
):
    """
    Poll jobs until they complete, fail, or timeout.

    Single Responsibility Principle: Only handles polling logic, not UI updates
    or status interpretation. Caller decides how to use the returned status.

    Args:
        jobs (list): List of AsyncResult objects to wait for
        query_names (list): List of corresponding query names (for logging)
        poll_interval (float): How often to check job status (seconds)
        max_wait_time (int): Maximum time to wait before timeout (seconds)
        context (str): Context string for logging (e.g., page name)

    Returns:
        tuple: (status, message) where status is one of:
            - PAGE_STATUS_READY: All jobs completed successfully
            - PAGE_STATUS_FAILED: One or more jobs failed
            - PAGE_STATUS_TIMEOUT: Timeout reached before completion
    """
    start_time = time.time()

    while True:
        # Check for timeout
        if time.time() - start_time > max_wait_time:
            logging.warning(f"{context} - Timeout after {max_wait_time}s")
            return PAGE_STATUS_TIMEOUT, "Timeout"

        # Log progress
        if context:
            ready_count = sum(1 for j in jobs if j.successful())
            logging.info(f"{context}: {ready_count}/{len(jobs)} queries ready")
        else:
            logging.warning([(name, j.status) for name, j in zip(query_names, jobs)])

        # Check if all jobs succeeded
        if all(j.successful() for j in jobs):
            logging.info(f"{context} - All queries ready")
            return PAGE_STATUS_READY, "Ready"

        # Check if any jobs failed
        if any(j.failed() for j in jobs):
            logging.warning(f"{context} - Some queries failed")
            # Wait for all jobs to finish before returning
            wait_for_all_jobs_to_finish(jobs)
            return PAGE_STATUS_FAILED, "Failed"

        # Poll again after interval
        time.sleep(poll_interval)


def wait_for_all_jobs_to_finish(jobs, max_wait_time=MAX_QUERY_WAIT_TIME):
    """
    Wait for all jobs to reach terminal state (success or failure).

    Used to ensure we don't forget Celery jobs that are still running
    when some jobs have already failed.

    Args:
        jobs (list): List of AsyncResult objects
        max_wait_time (int): Maximum time to wait before giving up (seconds)
    """
    start_time = time.time()

    while True:
        # Check for timeout to prevent indefinite blocking
        if time.time() - start_time > max_wait_time:
            logging.warning(f"Timeout waiting for all jobs to finish after {max_wait_time}s")
            break

        num_succeeded = sum(1 for j in jobs if j.successful())
        num_failed = sum(1 for j in jobs if j.failed())
        num_total = num_failed + num_succeeded

        if num_total == len(jobs):
            # All jobs reached terminal state
            break

        time.sleep(FAILURE_WAIT_INTERVAL)


def forget_jobs(jobs):
    """
    Forget all jobs to free up Celery backend resources.

    Args:
        jobs (list): List of AsyncResult objects to forget

    Returns:
        list: List of forgotten job results (for chaining if needed)
    """
    return [j.forget() for j in jobs]
