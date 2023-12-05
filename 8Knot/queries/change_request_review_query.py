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
                    pr.pull_request_id,
                    pr.repo_id AS id,
                    pr.pr_created_at,
                    pr.pr_closed_at,
                    pr.pr_merged_at,
                    MIN(c.msg_timestamp) OVER (PARTITION BY pr.pull_request_id) AS first_response_timestamp,
                    MAX(c.msg_timestamp) OVER (PARTITION BY pr.pull_request_id) AS last_response_timestamp
                FROM
                    pull_requests pr
                LEFT JOIN comments c ON pr.pull_request_id = c.pull_request_id
                WHERE
                    pr.repo_id in ({str(repos)[1:-1]})
                    """

    try:
        dbm = AugurManager()
        df = dbm.run_query(query_string)

        # Convert timestamps to dates and handle UUID conversion if necessary
        df["pr_created_at"] = pd.to_datetime(df["pr_created_at"], utc=True).dt.date
        df["pr_closed_at"] = pd.to_datetime(df["pr_closed_at"], utc=True).dt.date
        df["pr_merged_at"] = pd.to_datetime(df["pr_merged_at"], utc=True).dt.date
        df["first_response_timestamp"] = pd.to_datetime(df["first_response_timestamp"], utc=True).dt.date
        df["last_response_timestamp"] = pd.to_datetime(df["last_response_timestamp"], utc=True).dt.date
        df = df[df.pr_created_at < dt.date.today()]
        df = df.reset_index(drop=True)

        # Serialize the DataFrame to be stored in Redis
        pic = io.BytesIO()
        df.to_feather(pic)
        pic.seek(0)
        serialized_df = pic.read()

    except KeyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - INCOMPLETE ENVIRONMENT")
        return False
    except SQLAlchemyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - COULDN'T CONNECT TO DB")
        raise

    # Store results in Redis
    cm_o = cm()
    ack = cm_o.setm(
        func=change_request_review_query,
        repos=repos,
        datas=serialized_df,
    )
    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")

    return ack
