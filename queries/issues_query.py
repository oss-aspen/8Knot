import logging
from db_manager.AugurInterface import AugurInterface
from app_global import celery_app
from cache_manager.cache_manager import CacheManager as cm
import pandas as pd


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def issues_query(self, dbmc, repos):
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

    logging.debug("ISSUES_DATA_QUERY - START")

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

    # logging.debug(query_string)

    # create database connection, load config, execute query above.
    dbm = AugurInterface()
    dbm.load_pconfig(dbmc)

    df_issues = dbm.run_query(query_string)

    df_issues = df_issues[df_issues["pull_request_id"].isnull()]
    df_issues = df_issues.drop(columns="pull_request_id")
    df_issues = df_issues.sort_values(by="created")

    df_issues = df_issues.reset_index()
    df_issues.drop("index", axis=1, inplace=True)

    # break apart returned data per repo
    # and temporarily store in List to be
    # stored in Redis.
    pic = []
    for i, r in enumerate(repos):
        # convert series to a dataframe
        c_df = pd.DataFrame(df_issues.loc[df_issues["id"] == r]).to_csv()

        # add pickled dataframe to list of pickled objects
        pic.append(c_df)

    del df_issues

    # store results in Redis
    cm_o = cm()
    ack = cm_o.setm(func=issues_query, repos=repos, datas=pic)

    logging.debug("ISSUES_DATA_QUERY - END")
    return ack
