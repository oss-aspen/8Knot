"""
    Visualization-centric implementation of sandiego-rh/sandiego/notebooks/commits_activity.py
    as it is needed for the overview page of explorer.
"""


"""
    Imports
"""
import pandas as pd
from app import augur_db


def process_data(df_commits):
    """
    @author: Cali Dolfi
    @includer: James Kunstle

    Data processing is a repeat of the processing
    that is done in the notebook where this work was
    originall done.

    Ref: https://github.com/sandiego-rh/sandiego/blob/main/notebooks/commits_activity.ipynb
    """

    # convert datetime to proper format
    df_commits["date_time"] = pd.to_datetime(df_commits["date"], format="%Y-%m-%d")

    # sort by date and reset index for clarity
    df_repo_focus = df_commits.sort_values(by="date_time")
    df_repo_focus = df_repo_focus.reset_index(drop=True)

    # fetch all the unique commit IDs and drop the redundant ones
    df_commits_unique = df_repo_focus.drop(columns=["file"])
    agg_fun = {
        "repo_name": "first",
        "commits": "first",
        "lines_added": "sum",
        "lines_removed": "sum",
        "date": "first",
        "date_time": "first",
    }
    df_commits_unique = df_commits_unique.groupby(
        df_commits_unique["commits"]
    ).aggregate(agg_fun)
    df_commits_unique = df_commits_unique.reset_index(drop=True)

    repo_week_commits = (
        df_commits_unique["date_time"]
        .groupby(df_commits_unique.date_time.dt.to_period("W"))
        .agg("count")
    )
    return repo_week_commits


def _build_where_statement(repos: list, base: str):
    """
    @author Cali Dolfi, James Kunstle

    Use a base SQL 'WHERE' boolean and a list of repo_id's
    to build a mutually-inclusive string of all repos.
    """
    out = base
    for idx, repo in enumerate(repos):
        out += str(repo)
        if idx < len(repos) - 1:
            out += "\n\t\tOR " + base

    return out


def ret_df(repos: str, config: str):
    """
    @author Cali Dolfi, James Kunstle

    Returns the Dataframe expected of this query
    based on the list of repos that are passed.
    """

    if len(repos) == 0:
        return None

    # build the mutually inclusive string of repos that we want to execute our
    # query on
    repo_string = _build_where_statement(repos, "c.repo_id = ")

    query_string = f"""
                    SELECT
                        r.repo_name,
                        c.cmt_commit_hash AS commits,
                        c.cmt_id AS file, 
                        c.cmt_added AS lines_added,
                        c.cmt_removed AS lines_removed,
                        c.cmt_author_date AS date
                    FROM
                        repo r,
                        commits c
                    WHERE
                        r.repo_id = c.repo_id AND
                        {repo_string}
                    """

    # get the raw dataframe from our query output
    query_df = augur_db.run_query(query_string)

    # process the raw dataframe and output the processed data.
    return process_data(query_df)
