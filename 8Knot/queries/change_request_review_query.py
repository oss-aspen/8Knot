import logging
import pandas as pd
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import io
import datetime as dt
from sqlalchemy.exc import SQLAlchemyError

QUERY_NAME = "CRR"


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def change_request_review_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for change request review data.

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
                        pr.pr_src_number,
                        pr.pr_created_at AS pr_created,
                        pr.pr_closed_at AS pr_closed,
                        pr.pr_merged_at AS pr_merged,
                        rpr.review_id,
                        rpr.review_submitted_at,
                        rpr.review_status,
                        rpr.reviewer_id,
                        CASE 
                            WHEN rpr.reviewer_id IS NOT NULL THEN 'Human'
                            ELSE 'Bot'
                        END AS reviewer_type,
                        -- Additional fields as necessary
                    FROM
                        pull_requests pr
                    LEFT JOIN
                        repo_pull_request_reviews rpr ON pr.pull_request_id = rpr.pull_request_id
                    WHERE
                        pr.repo_id in ({str(repos)[1:-1]})
                    """

    try:
        dbm = AugurManager()
        engine = dbm.get_engine()
    except KeyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - INCOMPLETE ENVIRONMENT")
        return False
    except SQLAlchemyError:
        logging.error(f"{QUERY_NAME}_DATA_QUERY - COULDN'T CONNECT TO DB")
        raise SQLAlchemyError("DBConnect failed")

    df = dbm.run_query(query_string)

    # Store results in Redis
    cm_o = cm()
    ack = cm_o.setm(
        func=change_request_review_query,
        repos=repos,
        datas=[df.to_dict('records')],
    )

    logging.warning(f"{QUERY_NAME}_DATA_QUERY - END")
    return ack
