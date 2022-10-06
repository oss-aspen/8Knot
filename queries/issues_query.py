import logging
import pandas as pd
from db_manager.AugurInterface import AugurInterface


def issues_query(dbmc, repo_ids):
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

    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    query_string = f"""
                    SELECT
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
                        i.repo_id in({repo_statement})
                    """

    # create database connection, load config, execute query above.
    dbm = AugurInterface()
    dbm.load_pconfig(dbmc)
    df_issues = dbm.run_query(query_string)

    df_issues = df_issues[df_issues["pull_request_id"].isnull()]
    df_issues = df_issues.drop(columns="pull_request_id")
    df_issues = df_issues.sort_values(by="created")

    df_issues = df_issues.reset_index()
    df_issues.drop("index", axis=1, inplace=True)

    logging.debug("ISSUES_DATA_QUERY - END")

    return df_issues.to_dict("records")
