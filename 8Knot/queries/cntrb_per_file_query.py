import logging
import pandas as pd
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError

QUERY_NAME = "CNTRB_PER_FILE"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def cntrb_per_file_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database to get contributors per file data.

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
                    prf.pr_file_path as file_path,
                    pr.repo_id as ID,
                    string_agg(DISTINCT CAST(pr.pr_augur_contributor_id AS varchar(15)), ',') AS cntrb_ids
                FROM
                    pull_requests pr,
                    pull_request_files prf
                WHERE
                    pr.pull_request_id = prf.pull_request_id AND
                    pr.repo_id in ({str(repos)[1:-1]})
                GROUP BY prf.pr_file_path, pr.repo_id
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

    # pandas column and format updates
    df["cntrb_ids"] = df["cntrb_ids"].str.split(",")
    df = df.reset_index()
    df.drop("index", axis=1, inplace=True)
    # df.drop(["id"], axis=1, inplace=True)
    """Commonly used df updates:

    df["cntrb_id"] = df["cntrb_id"].astype(str)  # contributor ids to strings
    df["cntrb_id"] = df["cntrb_id"].str[:15]
    df = df.sort_values(by="created")
    df = df.reset_index()
    df = df.reset_index(drop=True)

    """

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
        func=cntrb_per_file_query,
        repos=repos,
        datas=pic,
    )
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")

    return ack
