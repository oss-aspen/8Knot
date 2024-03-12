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
def affiliation_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for organization affiliation data.

    Explorer_contributor_actions is a materialized view on the database for quicker run time and
    may not be in your augur database. The SQL query content can be found
    in docs/explorer_contributor_actions.sql

    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')

    """
    logging.warning(f"{affiliation_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = f"""
                    SELECT
                        left(c.cntrb_id::text, 15), -- first 15 characters of the uuid
                        timezone('utc', c.created_at) AS created_at,
                        c.repo_id,
                        c.login,
                        c.action,
                        c.rank,
                        con.cntrb_company,
                        string_agg(ca.alias_email, ' , ' order by ca.alias_email) as email_list
                    FROM
                        explorer_contributor_actions c
                    JOIN contributors_aliases ca
                        ON c.cntrb_id = ca.cntrb_id
                    JOIN contributors con
                        ON c.cntrb_id = con.cntrb_id
                    WHERE
                        c.repo_id in %s
                        and timezone('utc', c.created_at) < now() -- created_at is a timestamptz value
                        -- don't need to check non-null for created_at because it's non-null by definition.
                    GROUP BY c.cntrb_id, c.created_at, c.repo_id, c.login, c.action, c.rank, con.cntrb_company
                    ORDER BY
                        c.created_at
                    """

    # used for caching
    func_name = affiliation_query.__name__

    # raises Exception on failure. Returns nothing.
    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
    )
    """
    Old post-processing steps:

    # reformat cntrb_id
    df["cntrb_id"] = df["cntrb_id"].astype(str)
    df["cntrb_id"] = df["cntrb_id"].str[:15]

    df = df.sort_values(by="created")

    # change to compatible type and remove all data that has been incorrectly formatted
    df["created"] = pd.to_datetime(df["created"], utc=True).dt.date
    df = df[df.created < dt.date.today()]

    """
    logging.warning(f"{affiliation_query.__name__} COLLECTION - END")
