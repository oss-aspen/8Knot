import logging
from db_manager.augur_manager import AugurManager
from app import celery_app
from cache_manager.cache_manager import CacheManager as cm
import pandas as pd


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def issues_bugs_query(self, dbmc, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for issue data.

    Args:
    -----
        dbmc (AugurInterface): Handles connection to Augur database, executes queries and returns results.

        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """

    logging.debug("ISSUES_BUGS_QUERY - START")

    if len(repos) == 0:
        return None

    query_string = f"""
                    SELECT
                        l.label_text,
                        i.issue_id,
                        i.repo_id,
                        EXTRACT(epoch from age(i.closed_at, i.created_at)) as age,
                        i.created_at,
                        i.closed_at
                    FROM
                        issues i,
                        issue_labels l
                    WHERE
                        l.issue_id = i.issue_id AND
                        i.repo_id in ({str(repos)[1:-1]})
                    """

    # create database connection, load config, execute query above.
    dbm = AugurManager()
    dbm.load_pconfig(dbmc)
    # logging.debug("BUGZ q: " + query_string)
    df_cont = dbm.run_query(query_string)

    # break apart returned data per repo and temporarily store in List to be stored in Redis.
    pic = []
    for i, r in enumerate(repos):
        # convert series to a dataframe
        c_df = pd.DataFrame(df_cont.loc[df_cont["repo_id"] == r]).to_csv()

        # add pickled dataframe to list of pickled objects
        pic.append(c_df)

    del df_cont

    # store results in Redis
    cm_o = cm()

    # 'ack' is a boolean of whether data was set correctly or not.
    ack = cm_o.setm(func=issues_bugs_query, repos=repos, datas=pic)

    logging.debug("ISSUES_BUGS_QUERY - END")
    return ack
