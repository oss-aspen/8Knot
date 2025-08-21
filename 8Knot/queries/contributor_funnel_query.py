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
def contributor_engagement_query(self, repos):
    """
    (Worker Query)
    Executes a simple SQL query to fetch all contributor engagement data.
    The aggregation for the funnel chart will be done in Python.
    
    Args:
    -----
        repos ([str]): A list of repository IDs.
    
    Returns:
    --------
        None: The results are cached directly by the caching_wrapper.
    """
    logging.warning(f"{contributor_engagement_query.__name__} COLLECTION - START")

    if not repos:
        return None

    query_string = """
        SELECT
            repo_id,
            cntrb_id,
            d1_first_issue_created_at,
            d1_first_pr_opened_at,
            d1_first_pr_commented_at,
            d2_has_merged_pr,
            d2_created_many_issues,
            d2_total_comments,
            d2_has_pr_with_many_commits,
            d2_commented_on_multiple_prs
        FROM augur_data.contributor_engagement
        WHERE repo_id IN %s
    """

    func_name = contributor_engagement_query.__name__

    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
        n_repolist_uses=1, 
    )

    logging.warning(f"{contributor_engagement_query.__name__} COLLECTION - END")