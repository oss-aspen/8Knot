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
