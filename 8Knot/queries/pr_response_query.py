import logging
import pandas as pd
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError

QUERY_NAME = "PR_RESPONSE"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def pr_response_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for contributor data.

    This query gets the time to first response on a pr if it exists,
    if not the earliest_msg_timestamp is null

    Args:
    -----
        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - START")

    if len(repos) == 0:
        return None

    query_string = f"""
                    SELECT
                        pr.pull_request_id,
                        pr.repo_id AS ID,
                        min(M.msg_timestamp) AS earliest_msg_timestamp,
                        pr.pr_created_at,
                        pr.pr_closed_at
                    FROM
                        pull_requests pr
                    LEFT OUTER JOIN
                        (
                            SELECT
                                prr.pull_request_id AS pull_request_id,
                                m.msg_timestamp AS msg_timestamp
                            FROM
                                pull_request_review_message_ref prrmr,
                                pull_requests pr,
                                message m,
                                pull_request_reviews prr
                            WHERE
                                prrmr.pr_review_id = prr.pr_review_id AND
                                prrmr.msg_id = m.msg_id AND
                                prr.pull_request_id = pr.pull_request_id
                            UNION ALL
                            SELECT
                                prmr.pull_request_id AS pull_request_id,
                                m.msg_timestamp AS msg_timestamp
                            FROM
                                pull_request_message_ref prmr,
                                pull_requests pr,
                                message m
                            WHERE
                                prmr.pull_request_id = pr.pull_request_id AND
                                prmr.msg_id = m.msg_id
                        ) M
                        ON
                            M.pull_request_id = pr.pull_request_id
                    WHERE
                        pr.repo_id in ({str(repos)[1:-1]})
                    GROUP BY
                        pr.pull_request_id,
                        pr.repo_id,
                        pr.pr_created_at,
                        pr.pr_closed_at
                """

    try:
        dbm = AugurManager()
        engine = dbm.get_engine()
    except KeyError:
        # noack, data wasn't successfully set.
        logging.error(f"{QUERY_NAME}_DATA_QUERY - INCOMPLETE ENVIRONMENT")
        return False
    except SQLAlchemyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - COULDN'T CONNECT TO DB")
        # allow retry via Celery rules.
        raise SQLAlchemyError("DBConnect failed")

    df = dbm.run_query(query_string)

    # change to compatible type and remove all data that has been incorrectly formated
    df["pr_created_at"] = pd.to_datetime(df["pr_created_at"], utc=True).dt.date
    df = df[df.pr_created_at < dt.date.today()]

    pic = []

    for i, r in enumerate(repos):
        # convert series to a dataframe
        c_df = pd.DataFrame(df.loc[df["id"] == r]).reset_index(drop=True)

        # bytes buffer to be written to
        b = io.BytesIO()

        # write dataframe in feather format to BytesIO buffer
        bs = c_df.to_feather(b)

        # move head of buffer to the beginning
        b.seek(0)

        # write the bytes of the buffer into the array
        bs = b.read()
        pic.append(bs)

    del df

    # store results in Redis
    cm_o = cm()

    # 'ack' is a boolean of whether data was set correctly or not.
    ack = cm_o.setm(
        func=pr_response_query,
        repos=repos,
        datas=pic,
    )
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")

    return ack
