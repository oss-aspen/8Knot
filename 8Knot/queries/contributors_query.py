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
def contributors_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for contributor data.

    Explorer_contributor_actions is a materialized view on the database for quicker run time and
    may not be in your augur database. The SQL query content can be found
    in docs/materialized_views/explorer_contributor_actions.sql

    NOTE: FOR ANALYSIS, REQUIRES PRE-PROCESSING STEP:
        contributors_df_action_naming() in 8Knot/8Knot/pages/utils/preprocessing_utils.py


    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')

    """
    logging.warning(f"{contributors_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = f"""
                    SELECT
                        ca.repo_id,
                        ca.repo_name,
                        left(ca.cntrb_id::text, 15) as cntrb_id, -- first 15 characters of the uuid
                        timezone('utc', ca.created_at) AS created_at,
                        ca.login,
                        ca.action,
                        ca.rank
                    FROM
                        explorer_contributor_actions ca
                    WHERE
                        ca.repo_id in %s
                        and timezone('utc', ca.created_at) < now() -- created_at is a timestamptz value
                        -- don't need to check non-null for created_at because it's non-null by definition.
                """

    # used for caching
    func_name = contributors_query.__name__

    # raises Exception on failure. Returns nothing.
    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
    )

    """
    Old Post-processing steps

    # reformat cntrb_id
    df["cntrb_id"] = df["cntrb_id"].astype(str)
    df["cntrb_id"] = df["cntrb_id"].str[:15]

    # reformat cntrb_id
    df["cntrb_id"] = df["cntrb_id"].astype(str)
    df["cntrb_id"] = df["cntrb_id"].str[:15]

    # change to compatible type and remove all data that has been incorrectly formated
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.date
    df = df[df.created_at < dt.date.today()]

    Additional post-processing done on-the-fly in 8knot/pages/utils/preprocessing_utils.py
    """

    logging.warning(f"{contributors_query.__name__} COLLECTION - END")

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def contributors_funnel_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for contributor engagement funnel data.

    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.warning(f"{contributors_funnel_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = """
                    SELECT
                        ca.repo_id,
                        left(ca.cntrb_id::text, 15) as cntrb_id,
                        ca.login as username,
                        MAX(CASE WHEN ca.action = 'issue_opened' THEN 1 ELSE 0 END) as created_issue,
                        MAX(CASE WHEN ca.action = 'pull_request_open' THEN 1 ELSE 0 END) as opened_pr,
                        MAX(CASE WHEN ca.action = 'pull_request_comment' THEN 1 ELSE 0 END) as pr_commented
                    FROM
                        explorer_contributor_actions ca
                    WHERE
                        ca.repo_id in %s
                        and ca.action IN ('issue_opened', 'pull_request_open', 'pull_request_comment', 'commit')
                        and timezone('utc', ca.created_at) < now()
                    GROUP BY
                        ca.repo_id, ca.cntrb_id, ca.login
                """

    # used for caching
    func_name = contributors_funnel_query.__name__

    # raises Exception on failure. Returns nothing.
    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
    )

    logging.warning(f"{contributors_funnel_query.__name__} COLLECTION - END")












    # queries/contributors_query.py
# import logging
# from app import celery_app
# import cache_manager.cache_facade as cf
# import math # Added for calculating total batches

# # --- EXISTING QUERY 1 (UNCHANGED) ---
# # This query remains exactly as you provided it.
# @celery_app.task(bind=True, autoretry_for=(Exception,), exponential_backoff=2, retry_kwargs={"max_retries": 5}, retry_jitter=True)
# def contributors_query(self, repos):
#     logging.warning(f"{contributors_query.__name__} COLLECTION - START")
#     if len(repos) == 0: return None
#     query_string = f"SELECT ca.repo_id, ca.repo_name, left(ca.cntrb_id::text, 15) as cntrb_id, timezone('utc', ca.created_at) AS created_at, ca.login, ca.action, ca.rank FROM explorer_contributor_actions ca WHERE ca.repo_id in %s and timezone('utc', ca.created_at) < now()"
#     func_name = contributors_query.__name__
#     cf.caching_wrapper(func_name=func_name, query=query_string, repolist=repos)
#     logging.warning(f"{contributors_query.__name__} COLLECTION - END")


# # --- FUNNEL QUERY (MODIFIED WITH BATCH PROCESSING LOGIC) ---
# @celery_app.task(bind=True, autoretry_for=(Exception,), exponential_backoff=2, retry_kwargs={"max_retries": 5}, retry_jitter=True)
# def contributors_funnel_query(self, repos):
#     """
#     (Worker Query) This query provides the rich data for the Contributor Journey visualization.
#     IT NOW PROCESSES REPOSITORIES IN SMALL BATCHES to reduce database load and improve reliability.
#     """
#     logging.warning(f"{contributors_funnel_query.__name__} COLLECTION - START")
#     if not repos:
#         logging.warning("No repositories provided. Task ending.")
#         return None

#     # --- BATCHING LOGIC ---
#     # Define the size of each batch. A smaller number means more, smaller queries.
#     # 10 is a safe and reasonable starting point.
#     BATCH_SIZE = 10
#     total_repos = len(repos)
#     total_batches = math.ceil(total_repos / BATCH_SIZE)

#     logging.warning(f"Starting batch processing for {total_repos} repos in {total_batches} batches of size {BATCH_SIZE}.")

#     # The SQL query is defined once, outside the loop.
#     query_string = """
#         WITH filtered_actions AS (
#             SELECT * FROM explorer_contributor_actions WHERE repo_id IN %s
#         ),
#         all_contributors AS (
#             SELECT DISTINCT cntrb_id, login as username FROM filtered_actions
#         ),
#         d0_data AS (
#             SELECT login as username, MIN(created_at) AS first_engagement_date
#             FROM filtered_actions
#             WHERE action IN ('watch', 'fork', 'star')
#             GROUP BY login
#         ),
#         d1_data AS (
#             SELECT cntrb_id, MIN(created_at) AS first_contribution_date,
#                    COUNT(CASE WHEN action = 'issue_opened' THEN 1 END) as created_issue,
#                    COUNT(CASE WHEN action = 'pull_request_open' THEN 1 END) as opened_pr,
#                    COUNT(CASE WHEN action = 'pull_request_comment' THEN 1 END) as pr_commented
#             FROM filtered_actions
#             WHERE action IN ('issue_opened', 'pull_request_open', 'pull_request_comment')
#             GROUP BY cntrb_id
#         ),
#         d2_data AS (
#             SELECT cntrb_id, COUNT(CASE WHEN action = 'pull_request_merged' THEN 1 END) AS pr_merged_count
#             FROM filtered_actions
#             WHERE action = 'pull_request_merged'
#             GROUP BY cntrb_id
#         ),
#         d3_data AS (
#             SELECT cntrb_id, MAX(created_at) AS last_activity_date
#             FROM filtered_actions
#             GROUP BY cntrb_id
#         )
#         SELECT
#             ac.cntrb_id,
#             ac.username,
#             d0.first_engagement_date,
#             d1.first_contribution_date,
#             COALESCE(d1.created_issue, 0) as created_issue,
#             COALESCE(d1.opened_pr, 0) as opened_pr,
#             COALESCE(d1.pr_commented, 0) as pr_commented,
#             COALESCE(d2.pr_merged_count, 0) as pr_merged_count,
#             d3.last_activity_date
#         FROM all_contributors ac
#         LEFT JOIN d0_data d0 ON ac.username = d0.username
#         LEFT JOIN d1_data d1 ON ac.cntrb_id = d1.cntrb_id
#         LEFT JOIN d2_data d2 ON ac.cntrb_id = d2.cntrb_id
#         LEFT JOIN d3_data d3 ON ac.cntrb_id = d3.cntrb_id;
#     """

#     func_name = contributors_funnel_query.__name__

#     # Loop through the list of repositories in chunks of BATCH_SIZE
#     for i in range(0, total_repos, BATCH_SIZE):
#         # Create a small batch of repository IDs
#         batch = repos[i:i + BATCH_SIZE]
        
#         batch_num = (i // BATCH_SIZE) + 1
#         logging.warning(f"Processing Batch {batch_num}/{total_batches} for repos: {batch}")

#         try:
#             # Call the caching wrapper for EACH small batch
#             cf.caching_wrapper(func_name=func_name, query=query_string, repolist=batch)
#             logging.warning(f"Batch {batch_num}/{total_batches} completed successfully.")
#         except Exception as e:
#             logging.error(f"ERROR processing Batch {batch_num}/{total_batches}: {e}")
#             # Depending on desired behavior, you could either continue to the next batch
#             # or re-raise the exception to make the Celery task fail and retry.
#             # For robustness, we will log the error and continue.
#             continue
            
#     logging.warning(f"{contributors_funnel_query.__name__} COLLECTION - END")