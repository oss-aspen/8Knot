from dash import callback
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import sqlalchemy as salc
import logging
from app import engine, augur_db, entries, all_entries

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


@callback(
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
            opts = [i[1] for i in all_entries if search.lower() in i[0] or i[1] in bar_state]
            # opts = [i for i in entries if search in i or i in bar_state]
        else:
            opts = [i for i in entries if search in i]

        opts.sort(key=lambda item: (len(item), item))

        # arbitrarily 'small' number of matches returned..
        if len(opts) < 250:
            return [opts]
        else:
            return [opts[:250]]


# call back for repo selctions to feed into visualization call backs
@callback(
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
    logging.debug("SEARCHBAR_ORG_REPO_PARSING - START")
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
        logging.debug("SEARCHBAR_ORG_REPO_PARSING - END")
        return f"Your current selections is: {selections[1:-1]}", list(total_ids)
    elif len(value) == 0:
        raise dash.exceptions.PreventUpdate


# call back for commits query
@callback(Output("commits-data", "data"), Input("repo_choices", "data"))
def generate_commit_data(repo_ids):
    logging.debug("COMMITS_DATA_QUERY - START")
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

    logging.debug("COMMITS_DATA_QUERY - END")
    return df_commits.to_dict("records")


# call back for contributions query
@callback(Output("contributions", "data"), Input("repo_choices", "data"))
def generate_contributions_data(repo_ids):
    logging.debug("CONTRIBUTIONS_DATA_QUERY - START")
    repo_statement = str(repo_ids)
    repo_statement = repo_statement[1:-1]

    contributions_query = salc.sql.text(
        f"""SELECT * FROM augur_data.explorer_contributor_actions WHERE repo_id in({repo_statement})"""
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
    logging.debug("CONTRIBUTIONS_DATA_QUERY - END")
    return df_cont.to_dict("records")


# call back for issue query
@callback(Output("issues-data", "data"), Input("repo_choices", "data"))
def generate_issues_data(repo_ids):

    logging.debug("ISSUES_DATA_QUERY - START")

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

    logging.debug("ISSUES_DATA_QUERY - END")

    return df_issues.to_dict("records")


@callback(Output("help-alert", "is_open"), Input("search-help", "n_clicks"), State("help-alert", "is_open"))
def show_help_alert(n_clicks, openness):
    if n_clicks == 0:
        return dash.no_update
    # switch the openness parameter, allows button to also
    # dismiss the Alert.
    return not openness
