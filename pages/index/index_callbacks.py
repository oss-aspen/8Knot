from datetime import datetime, timedelta
import re
import os
import time
import logging
from celery.result import AsyncResult
import dash_bootstrap_components as dbc
import dash
from dash import html, callback
from dash.dependencies import Input, Output, State
from app import augur
from cache_manager.cache_manager import CacheManager as cm
from queries.issues_query import issues_query as iq
from queries.commits_query import commits_query as cq
from queries.contributors_query import contributors_query as cnq
from queries.prs_query import prs_query as prq
from queries.company_query import company_query as cmq


# list of queries to be run
QUERIES = [iq, cq, cnq, prq, cmq]

# check if login has been enabled in config
login_enabled = os.getenv("AUGUR_LOGIN_ENABLED", "False") == "True"


@callback(
    [
        Output("nav-login-container", "children"),
        Output("login-popover", "is_open"),
    ],
    Input("augur_username_dash_persistence", "data"),
    State("login-succeeded", "data"),
)
def login_username_button(username, login_succeeded):
    """Sets logged-in-status component in top left of page.

    If a non-null username is known then we're logged in so we provide
    the user a button to go to Augur. Otherwise, we redirect them to login.

    This callback also sets a login_failure popover depending on whether
    a requested login succeeded.

    Args:
        username (str | None): Username of user or None
        login_succeeded (bool): Error enabled if login failed.

    Returns:
        _type_: _description_
    """

    if username:
        navlink = [
            dbc.NavLink(
                f"{username}",
                href=augur.user_account_endpoint,
                id="login-navlink",
            ),
        ]
    else:
        navlink = [
            dbc.NavLink(
                "Augur log in/sign up",
                href=augur.user_auth_endpoint,
                id="login-navlink",
            ),
        ]

    return navlink, not login_succeeded


@callback(
    [
        Output("augur_username_dash_persistence", "data"),
        Output("augur_user_bearer_token_dash_persistence", "data"),
        Output("augur_token_expiration_dash_persistence", "data"),
        Output("augur_refresh_token_dash_persistence", "data"),
        Output("augur_user_groups_dash_persistence", "data"),
        Output("augur_user_group_options_dash_persistence", "data"),
        Output("refresh-groups", "data"),
        Output("url", "search"),
        Output("login-succeeded", "data"),
    ],
    [
        Input("url", "href"),
        State("url", "search"),
        State("refresh-groups", "data"),
        State("augur_username_dash_persistence", "data"),
        State("augur_user_bearer_token_dash_persistence", "data"),
        State("augur_token_expiration_dash_persistence", "data"),
        State("augur_refresh_token_dash_persistence", "data"),
    ],
)
def get_augur_user_preferences(
    this_url,
    search_val,
    refresh_groups,
    username,
    bearer_token,
    expiration,
    refresh,
):
    """Handles logging in when the user navigates to application.

    If the user is navigating to application with a fresh tab, the app
    tries to log in with credentials (bearer token) if they're present and valid.

    If credentials are valid and user is logged in, user's groups are retrieved from
    Augur front-end and stored in their session.

    This function will be invoked any time a page is switched in the app, including when
    the application is accessed via redirect from Augur or on refresh.

    Args:
        this_url (str): current full href
        search_val (str): query strings to HREF
        refresh_groups (bool): whether we should refresh user's preferences
        username (str): stored username
        bearer_token (str): stored bearer token
        expiration (str): bearer token expiration date
        refresh (str): refresh token for bearer token

    Raises:
        dash.exceptions.PreventUpdate: if we're just switching between pages, don't update anything

    Returns:
        augur_username_dash_persistence (str): username
        augur_user_bearer_token_dash_persistence (str): bearer token
        augur_token_expiration_dash_persistence (str): bearer token expiration
        augur_refresh_token_dash_persistence (str): refresh token for bearer token
        augur_user_groups_dash_persistence (str): user's groups
        augur_user_group_options_dash_persistence (str): possible groups from source DB
        refresh-groups (bool): whether we should refresh user's preferences
        search_val (str): query strings to HREF- remove on login to fix refresh bug
        login-succeeded (bool):
    """

    # used to extract auth from URL
    code_pattern = re.compile(r"\?code=([0-9A-z]+)", re.IGNORECASE)

    # output values when login isn't possible
    no_login = [
        "",  # username
        "",  # bearer token
        "",  # bearer token expiration
        "",  # refresh token
        {},  # user groups
        [],  # user group options
        False,  # fetch groups?
        "",  # search (code_val) removed once logged in
    ]
    # ^note about 'search' above- we're removing it when this function returns
    # so that on refresh the logic below won't trigger another login try if the
    # user tries to refresh while still on the page redirected-to from Augur authorization.

    # URL-triggered callback
    if dash.ctx.triggered_id == "url":
        code_val = re.search(code_pattern, search_val)

        # always go through this path if login not enabled
        if (not refresh_groups and not code_val) or (not login_enabled):
            logging.debug("LOGIN: Page Switch")
            # code_val is Falsy when it's None, so we want to pass
            # this check when it's None

            # this happens when the user is just going between pages
            # so we don't need to do anything.
            raise dash.exceptions.PreventUpdate

        if code_val:
            logging.debug("LOGIN: Redirect from Augur; Code pattern in href")
            # the user has just redirected from Augur so we know
            # that we need to get their new credentials.

            auth = code_val.groups()[0]

            # use the auth token to get the bearer token
            username, bearer_token, expiration, refresh = augur.auth_to_bearer_token(auth)

            # if we try to log in with the auth token we just get and the login fails, we
            # tell the user with a popover and do nothing.

            if not all([username, bearer_token, expiration, refresh]):
                return no_login + [
                    False,
                ]  # standard no-login plus login failed
            else:
                expiration = datetime.now() + timedelta(seconds=expiration)

        elif refresh_groups:

            if expiration and bearer_token:
                logging.debug("LOGIN: Warm Startup; expiration and bearer token in localStorage")
                # warm startup, bearer token could still be valid

                if datetime.now() > datetime.strptime(expiration, "%Y-%m-%dT%H:%M:%S.%f"):
                    logging.debug("LOGIN: Expired Bearer Token")

                    return no_login + [
                        True,
                    ]  # standard no-login, login didn't succeed, but it didn't fail, so don't need popover
            else:
                logging.debug("LOGIN: Cold Startup; no credentials available")
                # no previous credentials, can't do anything w/o login.
                return no_login + [
                    True,
                ]  # standard no-login, login didn't succeed, but it didn't fail, so don't need popover

        # we'll have either gotten a new bearer token if we're coming from augur
        # or we'll have verified that bearer_token should be valid
        augur_users_groups = augur.make_user_request(access_token=bearer_token)
        if not augur_users_groups or (augur_users_groups.get("status") != "success"):
            logging.debug("LOGIN: Failure")
            logging.error("Error logging in to Augur- couldn't complete user's Groups request.")
            return no_login + [
                False,
            ]  # standard no-login plus login failed

        # structure of the incoming data
        # [{group_name: {favorited: False, repos: [{repo_git: asd;lfkj, repo_id=46555}, ...]}, ...]
        # creates the group_name->repo_list mapping and the searchbar options for augur user groups
        users_groups = {}
        users_group_options = []
        g = augur_users_groups.get("data")

        # each of the augur user groups
        for entry in g:

            # group has one key- the name.
            group_name: str = list(entry.keys())[0]

            # only one value per entry- {favorited: ..., repos: ...},
            # get the value component
            repo_list = list(entry.values())[0]["repos"]

            # get all of the repo_ids in the 'repos' part of the value
            # translated via the git url to the id's of the DB that's
            # backing the client application
            ids = []
            for repo in repo_list:
                # get the git url of the repo
                repo_git = repo.get("repo_git")
                # translate that natural key to the repo's ID in the primary database
                repo_id_translated = augur.repo_git_to_id(repo_git)
                # check if the translation worked.
                if repo_id_translated:
                    ids.append(repo_id_translated)
                else:
                    logging.error(f"Repo: {repo_git} not translatable to repo_id- source DB incomplete.")

            # using lower_name for convenience later- no .lower() calls
            lower_name = group_name.lower()

            # group_name->repo_list mapping
            users_groups[lower_name] = ids

            # searchbar options
            # user's groups are prefixed w/ username to guarantee uniqueness in searchbar
            users_group_options.append({"value": lower_name, "label": f"{username}_{group_name}"})

        logging.debug("LOGIN: Success")
        return (
            username,
            bearer_token,
            expiration,
            refresh,
            users_groups,
            users_group_options,
            False,  # refresh_groups
            "",  # reset search to empty post-login
            True,  # login succeeded
        )


@callback(
    [Output("projects", "data")],
    [Input("projects", "searchValue")],
    [
        State("projects", "value"),
        State("augur_user_group_options_dash_persistence", "data"),
    ],
)
def dynamic_multiselect_options(user_in: str, selections, augur_groups):

    """
    Ref: https://dash.plotly.com/dash-core-components/dropdown#dynamic-options

    For all of the possible repo's / orgs, check if the substring currently
    being searched is in the repo's name or if the repo / org name is
    in the current list of states selected. Add it to the list if it matches
    either of the options.
    """

    if not user_in:
        return dash.no_update

    options = augur.get_multiselect_options().copy()
    options = options + augur_groups

    # if the number of options changes then we're
    # adding AUGUR_ entries somewhere.

    if selections is None:
        selections = []

    # match lowercase inputs with lowercase possible values
    opts = [i for i in options if user_in.lower() in i["label"]]

    # sort matches by length
    opts = sorted(opts, key=lambda v: len(v["label"]))

    # always include the previous selections from the searchbar to avoid
    # those values being clobbered when we truncate the total length.
    # arbitrarily 'small' number of matches returned..
    if len(opts) < 100:
        return [opts + [v for v in options if v["value"] in selections]]

    else:
        return [opts[:100] + [v for v in options if v["value"] in selections]]


# callback for repo selections to feed into visualization call backs
@callback(
    [Output("results-output-container", "children"), Output("repo-choices", "data")],
    [
        Input("search", "n_clicks"),
        State("projects", "value"),
        State("augur_user_groups_dash_persistence", "data"),
    ],
)
def multiselect_values_to_repo_ids(n_clicks, user_vals, user_groups):
    if user_vals is None:
        raise dash.exceptions.PreventUpdate

    # individual repo numbers
    repos = [r for r in user_vals if isinstance(r, int)]
    logging.debug(f"REPOS: {repos}")

    # names of augur groups or orgs
    names = [n for n in user_vals if isinstance(n, str)]

    org_repos = [augur.org_to_repos(o) for o in names if augur.is_org(o)]
    # flatten list repo_ids in orgs to 1D
    org_repos = [v for l in org_repos for v in l]
    logging.debug(f"ORG_REPOS: {org_repos}")

    group_repos = [user_groups[g] for g in names if not augur.is_org(g)]
    # flatten list repo_ids in orgs to 1D
    group_repos = [v for l in group_repos for v in l]
    logging.debug(f"GROUP_REPOS: {group_repos}")

    # only unique repo ids
    all_repo_ids = list(set().union(*[repos, org_repos, group_repos]))
    logging.debug(f"SELECTED_REPOS: {all_repo_ids}")

    return "", all_repo_ids


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
