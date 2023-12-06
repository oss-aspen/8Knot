import logging
import pandas as pd
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError

QUERY_NAME = "change_request_review"

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def change_request_review_query(self, repos):
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - START")

    if len(repos) == 0:
        return None

    query_string = f"""
                SELECT
                    epr.pr_src_id,
                    epr.repo_id AS id,
                    epr.pr_created_at,
                    epr.pr_closed_at,
                    epr.pr_merged_at,
                    epr.days_to_close,
                    CASE
                        WHEN epr.days_to_first_response < 0 THEN NULL
                        ELSE epr.days_to_first_response
                    END as days_to_first_response,
                    CASE
                        WHEN epr.days_to_last_response < 0 THEN NULL
                        ELSE epr.days_to_last_response
                    END as days_to_last_response
                FROM
                    explorer_pr_response_times epr
                WHERE
                    epr.repo_id in ({str(repos)[1:-1]})
                """

    try:
        dbm = AugurManager()
        engine = dbm.get_engine()
    except KeyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - INCOMPLETE ENVIRONMENT")
        return False
    except SQLAlchemyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - COULDN'T CONNECT TO DB")
        raise

    df = dbm.run_query(query_string)
        
    if df is None:
        logging.error(f"No data returned for repos {repos}")
        return None

    # Convert timestamps to dates and handle UUID conversion if necessary
    df["pr_created_at"] = pd.to_datetime(df["pr_created_at"], utc=True).dt.date
    df["pr_closed_at"] = pd.to_datetime(df["pr_closed_at"], utc=True).dt.date
    df["pr_merged_at"] = pd.to_datetime(df["pr_merged_at"], utc=True).dt.date
    df = df[df.pr_created_at < dt.date.today()]
    df = df.reset_index(drop=True)

    # Serialize the DataFrame to be stored in Redis
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
        func=change_request_review_query,
        repos=repos,
        datas=pic,
    )
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")

    return ack
