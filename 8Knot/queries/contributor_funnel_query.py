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
def contributor_funnel_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for contributor funnel data.
    
    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.
    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.warning(f"{contributor_funnel_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = """
        WITH
          all_contributors AS (
            SELECT COUNT(DISTINCT cntrb_id) AS total_contributors
            FROM augur_data.contributor_engagement
            WHERE repo_id in %s
          ),
          basic_contributors AS (
            SELECT COUNT(DISTINCT cntrb_id) AS basic_count
            FROM augur_data.contributor_engagement
            WHERE repo_id in %s
              AND (d1_first_issue_created_at IS NOT NULL 
                   OR d1_first_pr_opened_at IS NOT NULL 
                   OR d1_first_pr_commented_at IS NOT NULL)
          ),
          deep_contributors AS (
            SELECT COUNT(DISTINCT cntrb_id) AS deep_count
            FROM augur_data.contributor_engagement
            WHERE repo_id in %s
              AND (d2_has_merged_pr = true 
                   OR d2_created_many_issues = true 
                   OR d2_total_comments >= 5
                   OR d2_has_pr_with_many_commits = true 
                   OR d2_commented_on_multiple_prs = true)
          )
        SELECT
          (SELECT total_contributors FROM all_contributors) AS "All Contributors",
          (SELECT basic_count FROM basic_contributors) AS "Basic Engagement",
          (SELECT deep_count FROM deep_contributors) AS "Deep Engagement"
    """

    # used for caching
    func_name = contributor_funnel_query.__name__

    # raises Exception on failure. Returns nothing.
    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
    )

    logging.warning(f"{contributor_funnel_query.__name__} COLLECTION - END")
