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
def cntrb_per_file_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database to get contributors per file data.

    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.warning(f"{cntrb_per_file_query.__name__}_DATA_QUERY - START")

    if len(repos) == 0:
        return None

    query_string = """
                SELECT
                    pr.repo_id as repo_id,
                    prf.pr_file_path as file_path,
                    string_agg(DISTINCT CAST(pr.pr_augur_contributor_id AS varchar(15)), ',') AS cntrb_ids,
                    string_agg(DISTINCT CAST(prr.cntrb_id AS varchar(15)), ',') AS reviewer_ids
                FROM
                    pull_requests pr,
                    pull_request_files prf,
                    pull_request_reviews prr
                WHERE
                    pr.pull_request_id = prf.pull_request_id AND
                    pr.pull_request_id = prr.pull_request_id AND
                    pr.repo_id in %s
                GROUP BY prf.pr_file_path, pr.repo_id
                """

    func_name = cntrb_per_file_query.__name__
    cf.caching_wrapper(func_name=func_name, query=query_string, repolist=repos)

    logging.warning(f"{func_name} COLLECTION - END")
    return 0
