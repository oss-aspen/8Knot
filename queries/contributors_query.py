import logging
import pandas as pd
from db_manager.AugurInterface import AugurInterface
from app_global import celery_app
from cache_manager.cache_manager import CacheManager as cm


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
        dbmc (AugurInterface): Handles connection to Augur database, executes queries and returns results.

        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.debug("CONTRIBUTIONS_DATA_QUERY - START")

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
    dbm = AugurInterface()
    dbm.load_pconfig(dbmc)
    df_cont = dbm.run_query(query_string)

    # update column values
    df_cont.loc[df_cont["action"] == "open_pull_request", "action"] = "Open PR"
    df_cont.loc[df_cont["action"] == "pull_request_comment", "action"] = "PR Comment"
    df_cont.loc[df_cont["action"] == "issue_opened", "action"] = "Issue Opened"
    df_cont.loc[df_cont["action"] == "issue_closed", "action"] = "Issue Closed"
    df_cont.loc[df_cont["action"] == "commit", "action"] = "Commit"
    df_cont.rename(columns={"action": "Action"}, inplace=True)

    df_cont = df_cont.reset_index()
    df_cont.drop("index", axis=1, inplace=True)

    pic = []

    for i, r in enumerate(repos):
        # convert series to a dataframe
        c_df = pd.DataFrame(df_cont.loc[df_cont["id"] == r]).to_csv()

        # add pickled dataframe to list of pickled objects
        pic.append(c_df)

    del df_cont

    # store results in Redis
    cm_o = cm()

    # 'ack' is a boolean of whether data was set correctly or not.
    ack = cm_o.setm(func=contributors_query, repos=repos, datas=pic)
    logging.debug("CONTRIBUTIONS_DATA_QUERY - END")

    return ack
