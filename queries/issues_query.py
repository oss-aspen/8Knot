import logging
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import pandas as pd
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError

QUERY_NAME = "ISSUE"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def issues_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for issue data.

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
                        r.repo_id as id,
                        r.repo_name,
                        i.issue_id AS issue,
                        i.gh_issue_number AS issue_number,
                        i.gh_issue_id AS gh_issue,
                        i.created_at AS created,
                        i.closed_at AS closed,
                        i.pull_request_id
                    FROM
                        repo r,
                        issues i
                    WHERE
                        r.repo_id = i.repo_id AND
                        r.repo_id in ({str(repos)[1:-1]})
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

    df = df[df["pull_request_id"].isnull()]
    df = df.drop(columns="pull_request_id")
    df = df.sort_values(by="created")

    # change to compatible type and remove all data that has been incorrectly formated
    df["created"] = pd.to_datetime(df["created"], utc=True).dt.date
    df = df[df.created < dt.date.today()]

    df = df.reset_index()
    df.drop("index", axis=1, inplace=True)

    # break apart returned data per repo
    # and temporarily store in List to be
    # stored in Redis.
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
        func=issues_query,
        repos=repos,
        datas=pic,
    )

    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")
    return ack
