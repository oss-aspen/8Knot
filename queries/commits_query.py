import logging
import pandas as pd
from db_manager.AugurInterface import AugurInterface


def commits_query(dbmc, repo_ids):
    """
    Worker query

    From an input list of repos, get relevant data about the
    commit history of those repos. Cache as dictionary in Redis.

    Expects dbm to be db_manager/AugurInterface.
    """
    logging.debug("COMMITS_DATA_QUERY - START")
    # query input format update
    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    query_string = f"""
                    SELECT
                        r.repo_name,
                        c.cmt_commit_hash AS commits,
                        c.cmt_id AS file,
                        c.cmt_added AS lines_added,
                        c.cmt_removed AS lines_removed,
                        c.cmt_author_date AS date
                    FROM
                        repo r
                    JOIN commits c
                    ON r.repo_id = c.repo_id
                    WHERE
                        c.repo_id in({repo_statement})
                    """

    # create database connection, load config, execute query above.
    dbm = AugurInterface()
    dbm.load_pconfig(dbmc)
    df_commits = dbm.run_query(query_string)

    logging.debug("COMMITS_DATA_QUERY - END")
    return df_commits.to_dict("records")
