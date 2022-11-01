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
def prs_query(self, dbmc, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for pull request data.

    Args:
    -----
        dbmc (AugurInterface): Handles connection to Augur database, executes queries and returns results.

        repo_ids ([str]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')
    """
    logging.debug("PR_DATA_QUERY - START")

    if len(repos) == 0:
        return None

    query_string = f"""
                    SELECT
                        r.repo_id as id,
                        r.repo_name,
                        pr.pull_request_id AS pull_request,
                        pr.pr_src_number,
                        pr.pr_created_at AS created,
                        pr.pr_closed_at AS closed,
                        pr.pr_merged_at  AS merged
                    FROM
                        repo r,
                        pull_requests pr
                    WHERE
                        r.repo_id = pr.repo_id AND
                        r.repo_id in ({str(repos)[1:-1]})
                    """

    # create database connection, load config, execute query above.
    dbm = AugurInterface()
    dbm.load_pconfig(dbmc)
    df_pr = dbm.run_query(query_string)

    # sort by the date created
    df_pr = df_pr.sort_values(by="created")

    # convert to datetime objects
    df_pr["created"] = pd.to_datetime(df_pr["created"], utc=True)
    df_pr["merged"] = pd.to_datetime(df_pr["merged"], utc=True)
    df_pr["closed"] = pd.to_datetime(df_pr["closed"], utc=True)
    df_pr = df_pr.reset_index()
    df_pr.drop("index", axis=1, inplace=True)

    # break apart returned data per repo
    # and temporarily store in List to be
    # stored in Redis.
    pic = []
    for i, r in enumerate(repos):
        # convert series to a dataframe
        c_df = pd.DataFrame(df_pr.loc[df_pr["id"] == r]).to_csv()

        # add pickled dataframe to list of pickled objects
        pic.append(c_df)

    del df_pr

    # store results in Redis
    cm_o = cm()
    ack = cm_o.setm(func=prs_query, repos=repos, datas=pic)

    logging.debug("PR_DATA_QUERY - END")
    return ack
