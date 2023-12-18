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
def pr_file_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for file pull request data.

    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.warning(f"{pr_file_query.__name__}_DATA_QUERY - START")

    if len(repos) == 0:
        return None

    query_string = """
                    SELECT
                        prf.pr_file_path as file_path,
                        pr.pull_request_id AS pull_request,
                        pr.repo_id as id
                    FROM
                        pull_requests pr,
                        pull_request_files prf
                    WHERE
                        pr.pull_request_id = prf.pull_request_id AND
                        pr.repo_id in %s
                """

    func_name = pr_file_query.__name__
    cf.caching_wrapper(func_name=func_name, query=query_string, repolist=repos)

    logging.warning(f"{func_name} COLLECTION - END")
    return 0
