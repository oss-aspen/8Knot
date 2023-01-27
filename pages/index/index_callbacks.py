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
        Output("augur_username", "data"),
        Output("augur_user_bearer_token", "data"),
        Output("augur_token_expiration", "data"),
        Output("augur_refresh_token", "data"),
        Output("augur_user_groups", "data"),
        Output("augur_user_group_options", "data"),
        Output("is-startup", "data"),
        Output("login-succeeded", "data"),
    ],
    [
        Input("url", "href"),
        State("url", "search"),
        State("is-startup", "data"),
        State("augur_username", "data"),
        State("augur_user_bearer_token", "data"),
        State("augur_token_expiration", "data"),
        State("augur_refresh_token", "data"),
    ],
)
def get_augur_user_preferences(
    this_url,
    search_val,
    is_startup,
    username,
    bearer_token,
    expiration,
    refresh,
):

    # used to extract auth from URL
    code_pattern = re.compile(r"\?code=([0-9A-z]+)", re.IGNORECASE)

    # output values when login isn't possible
    no_login = [
        dash.no_update,  # username
        dash.no_update,  # bearer token
        dash.no_update,  # bearer token expiration
        dash.no_update,  # refresh token
        dash.no_update,  # user groups
        dash.no_update,  # user group options
        False,  # startup state
    ]

    # URL-triggered callback
    if dash.ctx.triggered_id == "url":
        code_val = re.search(code_pattern, search_val)

        if not is_startup and not code_val:
            logging.debug("LOGIN: Page Switch")
            # code_val is Falsy when it's None, so we want to pass
            # this check when it's None

            # this happens when the user is just going between pages
            # so we don't need to do anything.
            raise dash.exceptions.PreventUpdate

        if code_val:
            logging.debug("LOGIN: Augur Redirect")
            # the user has just redirected from Augur so we know
            # that we need to get their new credentials.

            auth = code_val.groups()[0]

            # use the auth token to get the bearer token
            username, bearer_token, expiration, refresh = augur.auth_to_bearer_token(auth)

            logging.debug(f"USERNAME: {username}")
            logging.debug(f"BT: {bearer_token}")
            logging.debug(f"EXPIRATION: {expiration}")
            logging.debug(f"REFRESH: {refresh}")

            # if we try to log in with the auth token we just get and the login fails, we
            # tell the user with a popover and do nothing.

            if not all([username, bearer_token, expiration, refresh]):
                return no_login + [False]  # standard no-login plus login failed
            else:
                expiration = datetime.now() + timedelta(seconds=expiration)

        if is_startup:

            if expiration and bearer_token:
                logging.debug("LOGIN: Warm Startup")
                # warm startup, bearer token could still be valid

                logging.debug(expiration)
                logging.debug(type(expiration))

                logging.debug(datetime.now())
                logging.debug(type(datetime.now()))
                if datetime.now() > datetime.strptime(expiration, "%Y-%m-%dT%H:%M:%S.%f"):
                    # expiration should already be a datetime object
                    # reflecting the time at which the token will expire
                    logging.debug("LOGIN: Expired Bearer Token")
                    # check whether the current bearer token is valid (and exists)
                    # if invalid, just don't do anything and let the
                    # user login.
                    # TODO implement refresh token here
                return no_login + [
                    True
                ]  # standard no-login, login didn't succeed, but it didn't fail, so don't need popover
            else:
                logging.debug("LOGIN: Cold Startup")
                # no previous credentials, can't do anything w/o login.
                return no_login + [
                    True
                ]  # standard no-login, login didn't succeed, but it didn't fail, so don't need popover

        # we'll have either gotten a new bearer token if we're coming from augur
        # or we'll have verified that bearer_token should be valid
        augur_users_groups = augur.make_user_request(access_token=bearer_token)
        if not augur_users_groups:
            logging.debug("LOGIN: Failure")
            logging.error("Error logging in to Augur- couldn't complete user's Groups request.")
            return no_login + [False]  # standard no-login plus login failed

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

        logging.debug(f"LOGIN: Success- \n{users_group_options}")
        return (
            username,
            bearer_token,
            expiration,
            refresh,
            users_groups,
            users_group_options,
            False,  # is_startup
            True,  # login succeeded
        )


@callback(
    [Output("projects", "data")],
    [Input("projects", "searchValue")],
    [State("projects", "value"), State("augur_user_group_options", "data")],
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
        State("augur_user_groups", "data"),
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


@callback(
    Output("login-container", "children"),
    Input("augur_username", "data"),
)
def login_button(username):
    if not username:
        child = (
            dbc.Button(
                dbc.NavLink(
                    "Augur log in/sign up",
                    href=os.getenv(
                        "AUGUR_USER_AUTH_ENDPOINT",
                        f"http://chaoss.tv:5038/user/authorize?client_id={augur.app_id}&response_type=code",
                    ),
                    active=True,
                ),
                size="sm",
                color="primary",
                id="login-button",
            ),
        )
    else:
        child = [
            html.P(f"Welcome {username}! Need to go back to your augur account?"),
            dbc.NavLink(
                "Click here!",
                href=os.getenv(
                    "AUGUR_USER_ACCOUNT_ENDPOINT",
                    "http://chaoss.tv:5038/account/settings",
                ),
                id="navlink-button",
            ),
        ]
    return child


@callback(
    Output("nav-login-container", "children"),
    Input("augur_username", "data"),
    State("login-succeeded", "data"),
    State("url", "href"),
)
def login_logout_button(username, login_succeeded, href):

    if username:
        navlink = [
            dbc.NavLink(
                f"{username}",
                href="http://chaoss.tv:5038/account/settings",
                id="login-navlink",
            ),
            dbc.Button("Logout (In Dev.)", id="logout-button", color="danger", disabled=True),
        ]
    else:
        navlink = [
            dbc.NavLink(
                "Augur log in/sign up",
                href=f"http://chaoss.tv:5038/user/authorize?client_id={augur.app_id}&response_type=code",
                active=True,
                id="login-navlink",
            ),
        ]

    popover = [
        dbc.Popover(
            "Login Failed",
            body=True,
            is_open=not login_succeeded,
            placement="bottom",
            target="login-navlink",
        ),
    ]

    return navlink + popover
