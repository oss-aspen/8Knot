"""
Cache Invalidation Mechanism for 8Knot

This module provides functions to invalidate cached data when source data changes.
This ensures that visualizations show up-to-date information.
"""

import logging
import psycopg2 as pg
from cx_common import cache_cx_string
from datetime import datetime, timedelta


def invalidate_cache_for_repos(repo_ids, cache_func=None):
    """
    Invalidate cache entries for specific repositories.

    Args:
        repo_ids: List of repository IDs to invalidate
        cache_func: Optional specific cache function to invalidate.
                   If None, invalidates all caches for the repos.

    Returns:
        int: Number of cache entries invalidated
    """
    if not repo_ids:
        return 0

    try:
        conn = pg.connect(cache_cx_string)

        with conn.cursor() as cur:
            if cache_func:
                # Invalidate specific cache function
                cur.execute(
                    """
                    DELETE FROM cache_bookkeeping
                    WHERE repo_id = ANY(%s) AND cache_func = %s
                    """,
                    (repo_ids, cache_func),
                )
            else:
                # Invalidate all caches for these repos
                cur.execute(
                    """
                    DELETE FROM cache_bookkeeping
                    WHERE repo_id = ANY(%s)
                    """,
                    (repo_ids,),
                )

            deleted_count = cur.rowcount
            conn.commit()

        conn.close()
        logging.warning(f"Invalidated {deleted_count} cache entries for repos: {repo_ids}")
        return deleted_count

    except Exception as e:
        logging.error(f"Error invalidating cache: {e}")
        return 0


def invalidate_stale_cache(max_age_hours=24):
    """
    Invalidate cache entries older than specified age.

    Args:
        max_age_hours: Maximum age in hours before cache is considered stale

    Returns:
        int: Number of cache entries invalidated
    """
    try:
        conn = pg.connect(cache_cx_string)

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM cache_bookkeeping
                WHERE ts_cached < %s
                """,
                (cutoff_time,),
            )

            deleted_count = cur.rowcount
            conn.commit()

        conn.close()
        logging.warning(f"Invalidated {deleted_count} stale cache entries (older than {max_age_hours} hours)")
        return deleted_count

    except Exception as e:
        logging.error(f"Error invalidating stale cache: {e}")
        return 0


def invalidate_cache_for_func(cache_func):
    """
    Invalidate all cache entries for a specific cache function.

    Args:
        cache_func: Name of the cache function to invalidate

    Returns:
        int: Number of cache entries invalidated
    """
    try:
        conn = pg.connect(cache_cx_string)

        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM cache_bookkeeping
                WHERE cache_func = %s
                """,
                (cache_func,),
            )

            deleted_count = cur.rowcount
            conn.commit()

        conn.close()
        logging.warning(f"Invalidated {deleted_count} cache entries for function: {cache_func}")
        return deleted_count

    except Exception as e:
        logging.error(f"Error invalidating cache for function {cache_func}: {e}")
        return 0


def get_cache_status(repo_ids=None):
    """
    Get status of cache entries.

    Args:
        repo_ids: Optional list of repository IDs to check. If None, returns all.

    Returns:
        dict: Cache status information
    """
    try:
        conn = pg.connect(cache_cx_string)

        with conn.cursor() as cur:
            if repo_ids:
                cur.execute(
                    """
                    SELECT cache_func, COUNT(*) as count, MAX(ts_cached) as last_cached
                    FROM cache_bookkeeping
                    WHERE repo_id = ANY(%s)
                    GROUP BY cache_func
                    ORDER BY cache_func
                    """,
                    (repo_ids,),
                )
            else:
                cur.execute(
                    """
                    SELECT cache_func, COUNT(*) as count, MAX(ts_cached) as last_cached
                    FROM cache_bookkeeping
                    GROUP BY cache_func
                    ORDER BY cache_func
                    """
                )

            results = cur.fetchall()
            status = {
                row[0]: {
                    "count": row[1],
                    "last_cached": row[2].isoformat() if row[2] else None,
                }
                for row in results
            }

        conn.close()
        return status

    except Exception as e:
        logging.error(f"Error getting cache status: {e}")
        return {}
