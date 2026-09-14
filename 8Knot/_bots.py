from db_manager.augur_manager import AugurManager
from sqlalchemy.exc import SQLAlchemyError
import logging


def get_bots_list():
    query_string = f"""
                    SELECT
	                    cntrb_id
                    FROM
                        contributors c
                    WHERE
	                    gh_type LIKE 'Bot'
                """

    try:
        dbm = AugurManager()
        dbm.get_engine()
    except KeyError:
        logging.error("BOT_DATA_QUERY - INCOMPLETE ENVIRONMENT")
        raise
    except SQLAlchemyError:
        # Bot data is required at startup; there is no Celery retry here.
        logging.error("BOT_DATA_QUERY - COULDN'T CONNECT TO DB")
        raise

    df = dbm.run_query(query_string)
    # reformat cntrb_id
    df["cntrb_id"] = df["cntrb_id"].astype(str)
    df["cntrb_id"] = df["cntrb_id"].str[:15]
    bots_list = df["cntrb_id"].tolist()
    return bots_list
