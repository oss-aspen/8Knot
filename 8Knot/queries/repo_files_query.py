import logging
import pandas as pd
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError
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

    query_string = """
                    SELECT
                    rl.repo_id AS id,
                    r.repo_name,
                    r.repo_path,
                    rl.rl_analysis_date,
                    rl.file_path,
                    rl.file_name
                FROM
                    repo_labor rl,
                    repo r
                WHERE
                    rl.repo_id = r.repo_id AND
                    rl.repo_id in %s AND
                    rl.rl_analysis_date = (
                        SELECT
                            MAX(rl.rl_analysis_date)
                        FROM
                            repo_labor rl,
                            repo r
                        WHERE
                            rl.repo_id = r.repo_id AND
                            rl.repo_id in %s
                        )
                """

    func_name = repo_files_query.__name__
    cf.caching_wrapper(func_name=func_name, query=query_string, repolist=repos, n_repolist_uses=2)

    logging.warning(f"{func_name} COLLECTION - END")
    return 0
