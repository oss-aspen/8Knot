import logging
import cache_manager.cache_facade as cf
from app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def ossf_score_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for repo ossf scorecard information.

    Args:
    -----
        repos ([int]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')

    """
    logging.warning(f"{ossf_score_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = """
                SELECT
                    repo_id as id,
                    name,
                    score,
                    data_collection_date
                FROM
                    repo_deps_scorecard
                WHERE
                    repo_id IN %s
                """

    func_name = ossf_score_query.__name__

    # raises Exception on failure. Returns nothing.
    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
    )

    logging.warning(f"{ossf_score_query.__name__} COLLECTION - END")
