from dash import callback
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import sqlalchemy as salc
from app import app, engine, augur_db, entries

# helper function for repos to get repo_ids
def _parse_repo_choices(repo_git_set):

    repo_ids = []
    repo_names = []

    if len(repo_git_set) > 0:
        url_query = str(repo_git_set)
        url_query = url_query[1:-1]

        repo_query = salc.sql.text(
            f"""
        SET SCHEMA 'augur_data';
        SELECT DISTINCT
            r.repo_id,
            r.repo_name
        FROM
            repo r
        JOIN repo_groups rg 
        ON r.repo_group_id = rg.repo_group_id
        WHERE
            r.repo_git in({url_query})
        """
        )

        with engine.connect() as conn:
            t = conn.execute(repo_query)

        results = t.all()
        repo_ids = [row[0] for row in results]
        repo_names = [row[1] for row in results]

    return repo_ids, repo_names


# helper function for orgs to get repo_ids
def _parse_org_choices(org_name_set):
    org_repo_ids = []
    org_repo_names = []

    if len(org_name_set) > 0:
        name_query = str(org_name_set)
        name_query = name_query[1:-1]

        org_query = salc.sql.text(
            f"""
        SET SCHEMA 'augur_data';
        SELECT DISTINCT
            r.repo_id,
            r.repo_name
        FROM
            repo r
        JOIN repo_groups rg 
        ON r.repo_group_id = rg.repo_group_id
        WHERE
            rg.rg_name in({name_query})
        """
        )

        with engine.connect() as conn:
            t = conn.execute(org_query)

        results = t.all()
        org_repo_ids = [row[0] for row in results]
        org_repo_names = [row[1] for row in results]

    return org_repo_ids, org_repo_names


@app.callback(
    [Output("projects", "options")],
    [Input("projects", "search_value")],
    [State("projects", "value")],
)
def dropdown_dynamic_callback(search, bar_state):

    """
    Ref: https://dash.plotly.com/dash-core-components/dropdown#dynamic-options

    For all of the possible repo's / orgs, check if the substring currently
    being searched is in the repo's name or if the repo / org name is
    in the current list of states selected. Add it to the list if it matches
    either of the options.
    """

    if search is None or len(search) == 0:
        raise dash.exceptions.PreventUpdate
    else:
        if bar_state is not None:
            opts = [i for i in entries if search in i or i in bar_state]
        else:
            opts = [i for i in entries if search in i]

        # arbitrarily 'small' number of matches returned..
        if len(opts) < 250:
            return [opts]
        else:
            return [opts[:250]]


# call back for repo selctions to feed into visualization call backs
@app.callback(
    [Output("results-output-container", "children"), Output("repo_choices", "data")],
    Input("search", "n_clicks"),
    State("projects", "value"),
)
def update_output(n_clicks, value):
    if value is None:
        raise dash.exceptions.PreventUpdate

    """
    Section handles parsing the input repos / orgs when there is selected values
    """
    print("SEARCHBAR_ORG_REPO_PARSING - START")
    if len(value) > 0:
        repo_git_set = []
        org_name_set = []

        # split our processing of repos / orgs into two streams
        for r in value:
            if r.startswith("http"):
                repo_git_set.append(r)
            else:
                org_name_set.append(r)

        # get the repo_ids and the repo_names from our repo set of urls'
        repo_ids, repo_names = _parse_repo_choices(repo_git_set=repo_git_set)

        # get the repo_ids and the repo_names from our org set of names
        org_repo_ids, org_repo_names = _parse_org_choices(org_name_set=org_name_set)

        # collect all of the id's and names together
        total_ids = set(repo_ids + org_repo_ids)
        total_names = set(repo_names + org_repo_names)
        total_ids = list(total_ids)

        selections = str(value)

        # return the string that we want and return the list of the id's that we need for the other callback.
        print("SEARCHBAR_ORG_REPO_PARSING - END")
        return f"Your current selections is: {selections[1:-1]}", list(total_ids)
    elif len(value) == 0:
        raise dash.exceptions.PreventUpdate


# call back for commits query
@callback(Output("commits-data", "data"), Input("repo_choices", "data"))
def generate_commit_data(repo_ids):
    print("COMMITS_DATA_QUERY - START")
    # query input format update
    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    commits_query = f"""
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

    df_commits = augur_db.run_query(commits_query)

    print("COMMITS_DATA_QUERY - END")
    return df_commits.to_dict("records")


# call back for contributions query
@callback(Output("contributions", "data"), Input("repo_choices", "data"))
def generate_contributions_data(repo_ids):
    print("CONTRIBUTIONS_DATA_QUERY - START")
    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    contributions_query = salc.sql.text(
        f"""
        SELECT 
        * 
        FROM 
        (
            SELECT 
            ID AS cntrb_id, 
            A.created_at AS created_at, 
            date_part('month', A.created_at :: DATE) AS month, 
            date_part('year', A.created_at :: DATE) AS year, 
            A.repo_id, 
            repo_name, 
            full_name, 
            login, 
            ACTION, 
            rank() OVER (
                PARTITION BY id 
                ORDER BY 
                A.created_at ASC
            ) 
            FROM 
            (
                (
                SELECT 
                    canonical_id AS ID, 
                    created_at AS created_at, 
                    repo_id, 
                    'issue_opened' AS ACTION, 
                    contributors.cntrb_full_name AS full_name, 
                    contributors.cntrb_login AS login 
                FROM 
                    augur_data.issues 
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = issues.reporter_id 
                    LEFT OUTER JOIN (
                    SELECT 
                        DISTINCT ON (cntrb_canonical) cntrb_full_name, 
                        cntrb_canonical AS canonical_email, 
                        data_collection_date, 
                        cntrb_id AS canonical_id 
                    FROM 
                        augur_data.contributors 
                    WHERE 
                        cntrb_canonical = cntrb_email 
                    ORDER BY 
                        cntrb_canonical
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE 
                    repo_id in ({repo_statement}) 
                    AND pull_request IS NULL 
                GROUP BY 
                    canonical_id, 
                    repo_id, 
                    issues.created_at, 
                    contributors.cntrb_full_name, 
                    contributors.cntrb_login
                ) 
                UNION ALL 
                (
                    SELECT 
                    canonical_id AS ID, 
                    TO_TIMESTAMP(cmt_author_date, 'YYYY-MM-DD') AS created_at, 
                    repo_id, 
                    'commit' AS ACTION, 
                    contributors.cntrb_full_name AS full_name, 
                    contributors.cntrb_login AS login 
                    FROM 
                    augur_data.commits 
                    LEFT OUTER JOIN augur_data.contributors ON cntrb_email = cmt_author_email 
                    LEFT OUTER JOIN (
                        SELECT 
                        DISTINCT ON (cntrb_canonical) cntrb_full_name, 
                        cntrb_canonical AS canonical_email, 
                        data_collection_date, 
                        cntrb_id AS canonical_id 
                        FROM 
                        augur_data.contributors 
                        WHERE 
                        cntrb_canonical = cntrb_email 
                        ORDER BY 
                        cntrb_canonical
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                    WHERE 
                    repo_id in ({repo_statement}) 
                    GROUP BY 
                    repo_id, 
                    canonical_email, 
                    canonical_id, 
                    commits.cmt_author_date, 
                    contributors.cntrb_full_name, 
                    contributors.cntrb_login
                ) 
                UNION ALL 
                (
                    SELECT 
                    message.cntrb_id AS ID, 
                    created_at AS created_at, 
                    commits.repo_id, 
                    'commit_comment' AS ACTION, 
                    contributors.cntrb_full_name AS full_name, 
                    contributors.cntrb_login AS login 
                    FROM 
                    augur_data.commit_comment_ref, 
                    augur_data.commits, 
                    augur_data.message 
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id 
                    LEFT OUTER JOIN (
                        SELECT 
                        DISTINCT ON (cntrb_canonical) cntrb_full_name, 
                        cntrb_canonical AS canonical_email, 
                        data_collection_date, 
                        cntrb_id AS canonical_id 
                        FROM 
                        augur_data.contributors 
                        WHERE 
                        cntrb_canonical = cntrb_email 
                        ORDER BY 
                        cntrb_canonical
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                    WHERE 
                    commits.cmt_id = commit_comment_ref.cmt_id 
                    AND commits.repo_id in ({repo_statement}) 
                    AND commit_comment_ref.msg_id = message.msg_id 
                    GROUP BY 
                    ID, 
                    commits.repo_id, 
                    commit_comment_ref.created_at, 
                    contributors.cntrb_full_name, 
                    contributors.cntrb_login
                ) 
                UNION ALL 
                (
                    SELECT 
                    issue_events.cntrb_id AS ID, 
                    issue_events.created_at AS created_at, 
                    issues.repo_id, 
                    'issue_closed' AS ACTION, 
                    contributors.cntrb_full_name AS full_name, 
                    contributors.cntrb_login AS login 
                    FROM 
                    augur_data.issues, 
                    augur_data.issue_events 
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = issue_events.cntrb_id 
                    LEFT OUTER JOIN (
                        SELECT 
                        DISTINCT ON (cntrb_canonical) cntrb_full_name, 
                        cntrb_canonical AS canonical_email, 
                        data_collection_date, 
                        cntrb_id AS canonical_id 
                        FROM 
                        augur_data.contributors 
                        WHERE 
                        cntrb_canonical = cntrb_email 
                        ORDER BY 
                        cntrb_canonical
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                    WHERE 
                    issues.repo_id in ({repo_statement}) 
                    AND issues.issue_id = issue_events.issue_id 
                    AND issues.pull_request IS NULL 
                    AND issue_events.cntrb_id IS NOT NULL 
                    AND ACTION = 'closed' 
                    GROUP BY 
                    issue_events.cntrb_id, 
                    issues.repo_id, 
                    issue_events.created_at, 
                    contributors.cntrb_full_name, 
                    contributors.cntrb_login
                ) 
                UNION ALL 
                (
                    SELECT 
                    pr_augur_contributor_id AS ID, 
                    pr_created_at AS created_at, 
                    pull_requests.repo_id, 
                    'open_pull_request' AS ACTION, 
                    contributors.cntrb_full_name AS full_name, 
                    contributors.cntrb_login AS login 
                    FROM 
                    augur_data.pull_requests 
                    LEFT OUTER JOIN augur_data.contributors ON pull_requests.pr_augur_contributor_id = contributors.cntrb_id 
                    LEFT OUTER JOIN (
                        SELECT 
                        DISTINCT ON (cntrb_canonical) cntrb_full_name, 
                        cntrb_canonical AS canonical_email, 
                        data_collection_date, 
                        cntrb_id AS canonical_id 
                        FROM 
                        augur_data.contributors 
                        WHERE 
                        cntrb_canonical = cntrb_email 
                        ORDER BY 
                        cntrb_canonical
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                    WHERE 
                    pull_requests.repo_id in ({repo_statement}) 
                    GROUP BY 
                    pull_requests.pr_augur_contributor_id, 
                    pull_requests.repo_id, 
                    pull_requests.pr_created_at, 
                    contributors.cntrb_full_name, 
                    contributors.cntrb_login
                ) 
                UNION ALL 
                (
                    SELECT 
                    message.cntrb_id AS ID, 
                    msg_timestamp AS created_at, 
                    pull_requests.repo_id as repo_id, 
                    'pull_request_comment' AS ACTION, 
                    contributors.cntrb_full_name AS full_name, 
                    contributors.cntrb_login AS login 
                    FROM 
                    augur_data.pull_requests, 
                    augur_data.pull_request_message_ref, 
                    augur_data.message 
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id 
                    LEFT OUTER JOIN (
                        SELECT 
                        DISTINCT ON (cntrb_canonical) cntrb_full_name, 
                        cntrb_canonical AS canonical_email, 
                        data_collection_date, 
                        cntrb_id AS canonical_id 
                        FROM 
                        augur_data.contributors 
                        WHERE 
                        cntrb_canonical = cntrb_email 
                        ORDER BY 
                        cntrb_canonical
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                    WHERE 
                    pull_requests.repo_id in ({repo_statement}) 
                    AND pull_request_message_ref.pull_request_id = pull_requests.pull_request_id 
                    AND pull_request_message_ref.msg_id = message.msg_id 
                    GROUP BY 
                    message.cntrb_id, 
                    pull_requests.repo_id, 
                    message.msg_timestamp, 
                    contributors.cntrb_full_name, 
                    contributors.cntrb_login
                ) 
                UNION ALL 
                (
                    SELECT 
                    issues.reporter_id AS ID, 
                    msg_timestamp AS created_at, 
                    issues.repo_id as repo_id, 
                    'issue_comment' AS ACTION, 
                    contributors.cntrb_full_name AS full_name, 
                    contributors.cntrb_login AS login 
                    FROM 
                    issues, 
                    issue_message_ref, 
                    message 
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id 
                    LEFT OUTER JOIN (
                        SELECT 
                        DISTINCT ON (cntrb_canonical) cntrb_full_name, 
                        cntrb_canonical AS canonical_email, 
                        data_collection_date, 
                        cntrb_id AS canonical_id 
                        FROM 
                        augur_data.contributors 
                        WHERE 
                        cntrb_canonical = cntrb_email 
                        ORDER BY 
                        cntrb_canonical
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                    WHERE 
                    issues.repo_id in ({repo_statement}) 
                    AND issue_message_ref.msg_id = message.msg_id 
                    AND issues.issue_id = issue_message_ref.issue_id 
                    AND issues.pull_request_id = NULL 
                    GROUP BY 
                    issues.reporter_id, 
                    issues.repo_id, 
                    message.msg_timestamp, 
                    contributors.cntrb_full_name, 
                    contributors.cntrb_login
                )
            ) A, 
            repo 
            WHERE 
            ID IS NOT NULL 
            AND A.repo_id = repo.repo_id 
            GROUP BY 
            A.ID, 
            A.repo_id, 
            A.ACTION, 
            A.created_at, 
            repo.repo_name, 
            A.full_name, 
            A.login 
            ORDER BY 
            cntrb_id
        ) b 
        """
    )

    with engine.connect() as conn:
        df_cont = pd.read_sql(contributions_query, con=conn)

    # update column values
    df_cont.loc[df_cont["action"] == "open_pull_request", "action"] = "Open PR"
    df_cont.loc[df_cont["action"] == "pull_request_comment", "action"] = "PR Comment"
    df_cont.loc[df_cont["action"] == "issue_opened", "action"] = "Issue Opened"
    df_cont.loc[df_cont["action"] == "issue_closed", "action"] = "Issue Closed"
    df_cont.loc[df_cont["action"] == "commit", "action"] = "Commit"
    df_cont.rename(columns={"action": "Action"}, inplace=True)

    df_cont = df_cont.reset_index()
    df_cont.drop("index", axis=1, inplace=True)
    print("CONTRIBUTIONS_DATA_QUERY - END")
    return df_cont.to_dict("records")


# call back for issue query
@callback(Output("issues-data", "data"), Input("repo_choices", "data"))
def generate_issues_data(repo_ids):

    print("ISSUES_DATA_QUERY - START")

    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    issues_query = salc.sql.text(
        f"""
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
    )

    with engine.connect() as conn:
        df_issues = pd.read_sql(issues_query, con=conn)

    df_issues = df_issues[df_issues["pull_request_id"].isnull()]
    df_issues = df_issues.drop(columns="pull_request_id")
    df_issues = df_issues.sort_values(by="created")

    df_issues = df_issues.reset_index()
    df_issues.drop("index", axis=1, inplace=True)

    print("ISSUES_DATA_QUERY - END")

    return df_issues.to_dict("records")
