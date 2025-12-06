import logging
from app import celery_app
import cache_manager.cache_facade as cf


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def repo_files_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database to get the repo file data.

    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.warning(f"{repo_files_query.__name__}_DATA_QUERY - START")

    if len(repos) == 0:
        return None

    # NOTE: This query now uses the explorer_repo_files materialized view
    # which pre-computes the most recent file information for all repos.
    # This significantly improves performance by avoiding expensive
    # DISTINCT ON operations at query time.

    query_string = """
                    SELECT
                        repo_id AS id,
                        repo_name,
                        repo_path,
                        rl_analysis_date,
                        file_path,
                        file_name
                    FROM
                        augur_data.explorer_repo_files
                    WHERE
                        repo_id IN %s
                """

    func_name = repo_files_query.__name__
    cf.caching_wrapper(func_name=func_name, query=query_string, repolist=repos)

    logging.warning(f"{func_name} COLLECTION - END")
    return 0
