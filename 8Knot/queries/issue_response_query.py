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
def issue_response_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for issue response data.

    This query gets the messages that are in response to a issue if any exists,
    if not the msg_timestamp is null.

    Args:
    -----
        repos ([int]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')

    """
    logging.warning(f"{issue_response_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = """
                SELECT
                    i.issue_id,
                    i.repo_id AS repo_id,
                    i.cntrb_id  AS cntrb_id,
                    M.msg_timestamp,
                    M.msg_cntrb_id,
                    i.created_at ,
                    i.closed_at
                FROM
                    issues i
                LEFT OUTER JOIN
                    (
                        SELECT
                            imr.issue_id AS issue_id ,
                            m.msg_timestamp AS msg_timestamp,
                            m.cntrb_id AS msg_cntrb_id
                        FROM
                            issue_message_ref imr,
                            issues i,
                            message m
                        WHERE
                            i.issue_id = imr.issue_id AND
                            imr.msg_id = m.msg_id
                    ) M
                    ON
                        M.issue_id = i.issue_id
                WHERE
                    i.repo_id in %s
                """

    func_name = issue_response_query.__name__

    # raises Exception on failure. Returns nothing.
    cf.caching_wrapper(
        func_name=func_name,
        query=query_string,
        repolist=repos,
    )

    logging.warning(f"{issue_response_query.__name__} COLLECTION - END")
