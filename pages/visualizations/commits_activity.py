"""
    Visualization-centric implementation of sandiego-rh/sandiego/notebooks/commits_activity.py
    as it is needed for the overview page of explorer.
"""


"""
    Imports
"""
import re
import psycopg2
import pandas as pd 
import sqlalchemy as salc
import json
import os
import datetime


def get_engine():
    with open("./config_temp.json") as config_file:
        config = json.load(config_file)

    database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

    dbschema='augur_data'
    engine = salc.create_engine(
        database_connection_string,
        connect_args={'options': '-csearch_path={}'.format(dbschema)})

    return engine

def repo_name_to_id(engine, repo_name):
    repo_query = salc.sql.text(f"""
                SET SCHEMA 'augur_data';
                SELECT 
                b.repo_id
            FROM
                repo_groups a,
                repo b
            WHERE
                a.repo_group_id = b.repo_group_id AND
                b.repo_name = \'{repo_name}\'
    """)

    t = engine.execute(repo_query)
    repo_id =  t.mappings().all()[0].get('repo_id')
    print('repo_id')
    print(repo_id)
    return repo_id

def run_query(engine, repo_id):
    df_commits = pd.DataFrame()

    pr_query = salc.sql.text(f"""
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
        """)
    df_current_repo = pd.read_sql(pr_query, con=engine)
    df_commits = pd.concat([df_commits, df_current_repo])

    df_commits = df_commits.reset_index()
    df_commits.drop("index", axis=1, inplace=True)

    return df_commits

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

def ret_df(repo):
    engine = get_engine()
    repo_id = repo_name_to_id(engine, repo)
    print("repo_id")
    print(repo_id)
    query_df = run_query(engine, repo_id)
    print("query df")
    print(query_df.head())
    return process_data(query_df)
