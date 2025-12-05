"""
Materialized View Refresh Strategy for 8Knot Heatmap Functionality

This module provides functions to refresh materialized views in the Augur database
that are used by the heatmap visualizations. These views need to be refreshed
periodically to ensure data accuracy.

The materialized views are:
- explorer_repo_files
- explorer_cntrb_per_file
- explorer_pr_files
"""

import logging
import psycopg2 as pg
from cx_common import init_cx_string
import os


def refresh_materialized_views(connection_string=None):
    """
    Refresh all materialized views used by heatmap visualizations.

    Args:
        connection_string: Optional connection string. If None, uses init_cx_string.

    Returns:
        bool: True if successful, False otherwise
    """
    if connection_string is None:
        connection_string = init_cx_string

    augur_schema = os.getenv("AUGUR_SCHEMA", "augur_data")

    views_to_refresh = [
        "explorer_repo_files",
        "explorer_cntrb_per_file",
        "explorer_pr_files",
    ]

    try:
        conn = pg.connect(connection_string)
        conn.autocommit = True

        with conn.cursor() as cur:
            for view_name in views_to_refresh:
                try:
                    logging.warning(f"Refreshing materialized view: {augur_schema}.{view_name}")
                    cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {augur_schema}.{view_name}")
                    logging.warning(f"Successfully refreshed {view_name}")
                except Exception as e:
                    # CONCURRENTLY requires unique index, fall back to regular refresh
                    if "concurrently" in str(e).lower():
                        logging.warning(f"CONCURRENTLY refresh failed for {view_name}, using regular refresh")
                        cur.execute(f"REFRESH MATERIALIZED VIEW {augur_schema}.{view_name}")
                        logging.warning(f"Successfully refreshed {view_name} (non-concurrent)")
                    else:
                        logging.error(f"Error refreshing {view_name}: {e}")
                        raise

        conn.close()
        logging.warning("All materialized views refreshed successfully")
        return True

    except Exception as e:
        logging.error(f"Error refreshing materialized views: {e}")
        return False


def check_materialized_view_status(connection_string=None):
    """
    Check the status of materialized views (populated or not).

    Args:
        connection_string: Optional connection string. If None, uses init_cx_string.

    Returns:
        dict: Status of each materialized view
    """
    if connection_string is None:
        connection_string = init_cx_string

    augur_schema = os.getenv("AUGUR_SCHEMA", "augur_data")

    views_to_check = [
        "explorer_repo_files",
        "explorer_cntrb_per_file",
        "explorer_pr_files",
    ]

    status = {}

    try:
        conn = pg.connect(connection_string)

        with conn.cursor() as cur:
            for view_name in views_to_check:
                cur.execute(
                    """
                    SELECT ispopulated, pg_size_pretty(pg_total_relation_size(%s))
                    FROM pg_matviews
                    WHERE schemaname = %s AND matviewname = %s
                    """,
                    (f"{augur_schema}.{view_name}", augur_schema, view_name),
                )
                result = cur.fetchone()
                if result:
                    status[view_name] = {
                        "populated": result[0],
                        "size": result[1] if result[1] else "0 bytes",
                    }
                else:
                    status[view_name] = {
                        "populated": False,
                        "size": "N/A (view not found)",
                    }

        conn.close()
        return status

    except Exception as e:
        logging.error(f"Error checking materialized view status: {e}")
        return {view: {"error": str(e)} for view in views_to_check}


if __name__ == "__main__":
    # Allow running as a script for manual refresh
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status = check_materialized_view_status()
        for view, info in status.items():
            print(f"{view}: {info}")
    else:
        success = refresh_materialized_views()
        sys.exit(0 if success else 1)
