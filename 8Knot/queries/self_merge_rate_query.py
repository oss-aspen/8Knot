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
def self_merge_rate_query(self, repos):
    """
    (Worker Query)
    Pull requests that have merged, with merger contributor id from the latest
    merge event
    """
    logging.warning(f"{self_merge_rate_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = """
        SELECT
            r.repo_id,
            r.repo_name,
            pr.pull_request_id,
            pr.pr_src_number,
            left(pr.pr_augur_contributor_id::text, 15) AS cntrb_id,
            pr.pr_created_at AS created_at,
            pr.pr_merged_at AS merged_at,
            me.merger_cntrb_id
        FROM repo r
        INNER JOIN pull_requests pr ON r.repo_id = pr.repo_id
        LEFT JOIN LATERAL (
            SELECT left(pre.cntrb_id::text, 15) AS merger_cntrb_id
            FROM pull_request_events pre
            WHERE pre.pull_request_id = pr.pull_request_id
              AND pre.action = 'merged'
            ORDER BY pre.created_at DESC NULLS LAST
            LIMIT 1
        ) me ON true
        WHERE r.repo_id IN %s
          AND pr.pr_merged_at IS NOT NULL
          AND pr.pr_merged_at < now()
        ORDER BY pr.pr_merged_at
        """

    func_name = self_merge_rate_query.__name__

    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
    )

    logging.warning(f"{self_merge_rate_query.__name__} COLLECTION - END")
