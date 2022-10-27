import logging
import pandas as pd
from db_manager.AugurInterface import AugurInterface


def issues_query(dbmc, repo):
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

    query_string = f"""
                    SELECT
                        --r.repo_name,
                        --i.issue_id AS issue,
                        --i.gh_issue_number AS issue_number,
                        --i.gh_issue_id AS gh_issue,
                        i.created_at AS created,
                        i.closed_at AS closed
                        --i.pull_request_id
                    FROM
                        repo r,
                        issues i
                    WHERE
                        r.repo_id = i.repo_id AND
                        i.repo_id = {repo}
                    """

    # create database connection, load config, execute query above.
    dbm = AugurInterface()
    dbm.load_pconfig(dbmc)

    df_issues = dbm.run_query(query_string)
    df_issues = df_issues.reset_index()
    
    # check if query returned any rows of data.
    # if there is no data, store no data -
    # the existence of a job's result being empty is still
    # useful for aggregation and informative to users.
    if df_issues.shape[0] > 0:
        # massage SQL timestampdz to Posix timestamp int64- much smaller than string or datetime object.
        df_issues["created"] = pd.to_datetime(df_issues["created"], utc=True).map(pd.Timestamp.timestamp).astype("int64")
        # coerce means that invalid values are set to 'NaT', handling the error naturally.
        df_issues["closed"] = pd.to_datetime(df_issues["closed"], utc=True, errors="coerce")
        print(type(df_issues["closed"]))
        df_issues["closed"] = df_issues["closed"].map(pd.Timestamp.timestamp).astype("int64")

    logging.debug("ISSUES_DATA_QUERY - END")
    return df_issues.to_dict("records")
