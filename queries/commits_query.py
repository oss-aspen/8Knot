import logging
from db_manager.augur_manager import AugurManager
from app import celery_app
import pandas as pd
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError

# DEBUGGING
import os

QUERY_NAME = "COMMITS"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def commits_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for commit data.

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

    # commenting-outunused query components. only need the repo_id and the
    # authorship date for our current queries. remove the '--' to re-add
    # the now-removed values.
    query_string = f"""
                    SELECT
                        distinct
                        r.repo_id AS id,
                        -- r.repo_name,
                        c.cmt_commit_hash AS commits,
                        -- c.cmt_id AS file,
                        -- c.cmt_added AS lines_added,
                        -- c.cmt_removed AS lines_removed,
                        c.cmt_author_email AS author_email,
                        c.cmt_author_date AS date,
                        c.cmt_author_timestamp AS author_timestamp,
                        c.cmt_committer_timestamp AS committer_timestamp

                    FROM
                        repo r
                    JOIN commits c
                        ON r.repo_id = c.repo_id
                    WHERE
                        c.repo_id in ({str(repos)[1:-1]})
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
    df["author_timestamp"] = pd.to_datetime(df["author_timestamp"], utc=True).dt.date
    df = df[df.author_timestamp < dt.date.today()]

    # break apart returned data per repo
    # and temporarily store in List to be
    # stored in Redis.
    pic = []
    for r in repos:
        # convert series to a dataframe
        # once we've stored the data by ID we no longer need the column.
        c_df = pd.DataFrame(df.loc[df["id"] == r].drop(columns=["id"])).reset_index(drop=True)

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
        func=commits_query,
        repos=repos,
        datas=pic,
    )

    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")
    return ack
