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
        # defensive- currently unreachable, since app.py:38-44 constructs an
        # AugurManager over the same credentials and sys.exit(1)s first.
        # falling through from here left dbm unbound, so the caller would have
        # seen a NameError rather than this.
        logging.error("BOT_DATA_QUERY - INCOMPLETE ENVIRONMENT")
        raise
    except SQLAlchemyError:
        # runs at import in the web process, so there's no Celery retry to
        # fall back on- fail the boot rather than serve unfiltered bot data.
        logging.error("BOT_DATA_QUERY - COULDN'T CONNECT TO DB")
        raise

    df = dbm.run_query(query_string)
    # reformat cntrb_id
    df["cntrb_id"] = df["cntrb_id"].astype(str)
    df["cntrb_id"] = df["cntrb_id"].str[:15]
    bots_list = df["cntrb_id"].tolist()
    return bots_list
