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
          stage0_new AS (
            SELECT COUNT(DISTINCT cntrb_id) AS total_contributors
            FROM augur_data.augur_new_contributors
            WHERE repo_id in %s
          ),
          stage1_basic AS (
            SELECT COUNT(DISTINCT cntrb_id) AS engaged_contributors
            FROM augur_data.d1_contributor_engagement
            WHERE repo_id in %s
          ),
          stage2_deep AS (
            SELECT COUNT(DISTINCT cntrb_id) AS deeply_engaged_contributors
            FROM augur_data.d2_contributor_engagement
            WHERE repo_id in %s
          )
        SELECT
          (SELECT total_contributors FROM stage0_new) AS "All New Contributors",
          (SELECT engaged_contributors FROM stage1_basic) AS "Basic Engagement",
          (SELECT deeply_engaged_contributors FROM stage2_deep) AS "Deeper Engagement"
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
