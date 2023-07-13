import logging
import pandas as pd
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt

QUERY_NAME = "CONTRIBUTOR"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def contributors_query(self, dbmc, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for contributor data.

    Args:
    -----
        dbmc (AugurManager): Handles connection to Augur database, executes queries and returns results.

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
                        repo_id as id,
                        cntrb_id,
                        created_at,
                        login,
                        action,
                        rank
                    FROM
                        augur_data.explorer_contributor_actions
                    WHERE
                        repo_id in ({str(repos)[1:-1]})
                """

    # create database connection, load config, execute query above.
    dbm = AugurManager()
    dbm.load_pconfig(dbmc)
    df = dbm.run_query(query_string)

    # update column values
    df.loc[df["action"] == "open_pull_request", "action"] = "Open PR"
    df.loc[df["action"] == "pull_request_comment", "action"] = "PR Comment"
    df.loc[df["action"] == "issue_opened", "action"] = "Issue Opened"
    df.loc[df["action"] == "issue_closed", "action"] = "Issue Closed"
    df.loc[df["action"] == "commit", "action"] = "Commit"
    df["cntrb_id"] = df["cntrb_id"].astype(str)  # contributor ids to strings
    df.rename(columns={"action": "Action"}, inplace=True)

    # change to compatible type and remove all data that has been incorrectly formated
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.date
    df = df[df.created_at < dt.date.today()]

    df = df.reset_index(drop=True)

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
        func=contributors_query,
        repos=repos,
        datas=pic,
    )
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")

    return ack
