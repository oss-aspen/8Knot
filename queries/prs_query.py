import logging
import pandas as pd
from db_manager.AugurInterface import AugurInterface


def prs_query(dbmc, repo):
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

    query_string = f"""
                    SELECT
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
                        r.repo_id = {repo}
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

    logging.debug("PR_DATA_QUERY - END")
    return df_pr.to_dict("records")
