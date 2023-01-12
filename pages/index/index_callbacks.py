from dash import callback
from dash.dependencies import Input, Output, State
from app import augur
from flask import request
import dash
import logging
from cache_manager.cache_manager import CacheManager as cm
from queries.issues_query import issues_query as iq
from queries.commits_query import commits_query as cq
from queries.contributors_query import contributors_query as cnq
from queries.prs_query import prs_query as prq
import time
from celery.result import AsyncResult

# list of queries to be run
QUERIES = [iq, cq, cnq, prq]

# helper function for repos to get repo_ids
def _parse_repo_choices(repo_git_set):
    # get repo values from repo dictionary
    repo_dict = augur.get_repo_dict()
    repo_values = [repo_dict[x] for x in repo_git_set]
    # values for the repo_ids and names
    repo_ids = [row[0] for row in repo_values]
    repo_names = [row[1] for row in repo_values]

    return repo_ids, repo_names


# helper function for orgs to get repo_ids
def _parse_org_choices(org_name_set):

    org_dict = augur.get_org_dict()
    repo_dict = augur.get_repo_dict()

    # get git urls for the repos in the organization, sum operater is used to flatten the 2D list to 1D
    org_repos = sum([org_dict[x] for x in org_name_set], [])
    # get repo values from repo dictionary
    repo_values = [repo_dict[x] for x in org_repos]
    # values for the repo_ids and names
    org_repo_ids = [row[0] for row in repo_values]
    org_repo_names = [row[1] for row in repo_values]

    return org_repo_ids, org_repo_names


@callback(
    [
        Output("projects", "options"),
        Output("projects", "value"),
        Output("users_augur_groups", "data"),
        Output("user_bearer_token", "data"),
    ],
    [
        Input("url", "href"),
        State("user_bearer_token", "data"),
        State("users_augur_groups", "data"),
    ],
)
def dropdown_startup(this_url, user_token, users_groups):

    if request.args.get("auth") is None:
        logging.debug("no auth in url")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # check if there user-defined groups already in cache
    # TODO: check if there's an update to the groups from last time

    # this won't be None (would have failed)
    auth = request.args.get("code")

    # use the auth token to get the bearer token
    username, bearer_token = augur.auth_to_bearer_token(auth)

    if username is not None:
        logging.debug(f"Logged in as: {username}")
        augur_users_groups = augur.make_user_request(bearer_token)
        logging.debug(augur_users_groups)
    else:
        logging.error("Login to Augur failed")

    # assume that response from augur w/ bearer_token is json w/ format
    # {group_name: [repo_list]}

    entries = augur.get_all_entries()
    # concat_values = entries + augur_user_groups
    # return concat_values, concat_values, augur_user_groups

    # TODO: update return to handle concat
    return [entries], [entries], dash.no_update, dash.no_update


@callback(
    [Output("projects", "options")],
    [Input("projects", "search_value")],
    [State("projects", "value")],
)
def dropdown_dynamic_callback(user_in, selections):

    """
    Ref: https://dash.plotly.com/dash-core-components/dropdown#dynamic-options

    For all of the possible repo's / orgs, check if the substring currently
    being searched is in the repo's name or if the repo / org name is
    in the current list of states selected. Add it to the list if it matches
    either of the options.
    """

    all_entries = augur.get_all_entries()

    if selections is None:
        selections = []

    if user_in is None or len(user_in) == 0:
        raise dash.exceptions.PreventUpdate
    else:
        # match lowercase inputs with lowercase possible values
        opts = [i[1] for i in all_entries if user_in.lower() in i[0]]

        # sort matches by length
        opts.sort(key=lambda item: (len(item), item))

        # always include the previous selections from the searchbar to avoid
        # those values being clobbered when we truncate the total length.
        # arbitrarily 'small' number of matches returned..
        if len(opts) < 250:
            return [opts + selections]
        else:
            return [opts[:250] + selections]


# callback for repo selections to feed into visualization call backs
@callback(
    [Output("results-output-container", "children"), Output("repo-choices", "data")],
    Input("search", "n_clicks"),
    State("projects", "value"),
)
def update_output(n_clicks, value):
    if value is None:
        logging.info("No update")
        return dash.exceptions.PreventUpdate, dash.exceptions.PreventUpdate

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
        logging.debug("=========================================================")
        return f"Your current selections is: {selections[1:-1]}", list(total_ids)
    elif len(value) == 0:
        return dash.exceptions.PreventUpdate, dash.exceptions.PreventUpdate


@callback(
    Output("help-alert", "is_open"),
    Input("search-help", "n_clicks"),
    State("help-alert", "is_open"),
)
def show_help_alert(n_clicks, openness):
    """Sets the 'open' state of a help message
    for the search bar to encourage users to check
    their spelling and to ask for data to be loaded
    if not available.

    Args:
        n_clicks (int): number of times 'help' button clicked.
        openness (boolean): whether help alert is currently open.

    Returns:
        dash.no_update | boolean: whether the help alert should be open.
    """
    if n_clicks == 0:
        return dash.no_update
    # switch the openness parameter, allows button to also
    # dismiss the Alert.
    return not openness


@callback(
    [Output("data-badge", "children"), Output("data-badge", "color")],
    Input("job-ids", "data"),
    background=True,
)
def wait_queries(job_ids):
    # TODO add docstring to function

    jobs = [AsyncResult(j_id) for j_id in job_ids]

    # default 'result_expires' for celery config is 86400 seconds.
    # so we don't have to check if the jobs exist. if this tasks
    # is enqueued 24 hours after the query-worker tasks finish
    # then we have a big problem. However, we should 'forget' all
    # results before we exit.

    while True:
        logging.info([j.status for j in jobs])

        # jobs are either all ready
        if all(j.successful() for j in jobs):
            logging.info([j.status for j in jobs])
            jobs = [j.forget() for j in jobs]
            return "Data Ready", "success"

        # or one of them has failed
        if any(j.failed() for j in jobs):

            # if a job fails, we need to wait for the others to finish before
            # we can 'forget' them. otherwise to-be-successful jobs will always
            # be forgotten if one fails.

            # tasks need to have either failed or succeeded before being forgotten.
            while True:
                num_succeeded = [j.successful() for j in jobs].count(True)
                num_failed = [j.failed() for j in jobs].count(True)
                num_total = num_failed + num_succeeded

                if num_total == len(jobs):
                    break

                time.sleep(4.0)

            jobs = [j.forget() for j in jobs]
            return "Data Incomplete- Retry", "danger"

        # pause to let something change
        time.sleep(2.0)


@callback(
    Output("job-ids", "data"),
    Input("repo-choices", "data"),
)
def run_queries(repos):
    """
    Executes queries defined in /queries against Augur
    instance for input Repos; caches results in redis per
    (query_function,repo) pair.

    Args:
        repos ([int]): repositories we collect data for.
    """

    # cache manager object
    cache = cm()

    # list of queries to process
    funcs = QUERIES

    # list of job promises
    jobs = []

    for f in funcs:

        # only download repos that aren't currently in cache
        not_ready = [r for r in repos if cache.exists(f, r) != 1]

        # add job to queue
        j = f.apply_async(args=(augur.package_config(), not_ready), queue="data")

        # add job promise to local promise list
        jobs.append(j)

    return [j.id for j in jobs]
