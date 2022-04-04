"""
    Visualization-centric implementation of sandiego-rh/sandiego/notebooks/commits_activity.py
    as it is needed for the overview page of explorer.
"""


"""
    Imports
"""
from .db_interface import AugurInterface as augi
import pandas as pd

def process_data(df_commits):
    # convert datetime to proper format
    df_commits['date_time'] = pd.to_datetime(df_commits['date'], format= '%Y-%m-%d')

    print("df_commits")
    print(df_commits.head())

    # sort by date and reset index for clarity
    df_repo_focus = df_commits.sort_values(by= "date_time")
    df_repo_focus = df_repo_focus.reset_index(drop=True)
    print("df_repo_focus")
    print(df_repo_focus.head())

    # fetch all the unique commit IDs and drop the redundant ones
    df_commits_unique = df_repo_focus.drop(columns = ['file'])
    agg_fun = {'repo_name': 'first',  'commits': 'first', 'lines_added': 'sum', 'lines_removed': 'sum', 
                            'date': 'first', 'date_time': 'first'}
    df_commits_unique = df_commits_unique.groupby(df_commits_unique['commits']).aggregate(agg_fun)
    df_commits_unique = df_commits_unique.reset_index(drop=True)


    repo_week_commits = df_commits_unique['date_time'].groupby(df_commits_unique.date_time.dt.to_period("W")).agg('count')
    return repo_week_commits

def ret_df(repo: str, config: str):
    aug = augi()
    aug.get_engine()
    repo_id: int = aug.repo_name_to_id(repo)

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
                        c.repo_id = \'{repo_id}\'
                    """
    query_df = aug.run_query(query_string)

    return process_data(query_df)
