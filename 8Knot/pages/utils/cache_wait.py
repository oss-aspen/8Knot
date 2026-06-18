"""Helpers for waiting on asynchronously populated cache rows."""

import logging
import os
import time

import cache_manager.cache_facade as cf


def _poll_seconds():
    """Return the current cache poll interval in seconds."""
    try:
        return max(float(os.getenv("CACHE_POLL_SECONDS", "0.5")), 0.1)
    except ValueError:
        return 0.5


def wait_for_cache(func_name, repolist, log_message):
    """Wait for cached rows with a small backoff to reduce database pressure."""
    wait_seconds = _poll_seconds()
    try:
        max_wait_seconds = max(wait_seconds, float(os.getenv("CACHE_MAX_POLL_SECONDS", "4.0")))
    except ValueError:
        max_wait_seconds = 4.0

    while cf.get_uncached(func_name=func_name, repolist=repolist):
        logging.info(log_message)
        time.sleep(wait_seconds)
        wait_seconds = min(wait_seconds * 1.5, max_wait_seconds)
