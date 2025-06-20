from datetime import datetime, timedelta
import re
import os
import time
import logging
import json
from celery.result import AsyncResult
import dash_bootstrap_components as dbc
import dash
from dash import callback
from dash.dependencies import Input, Output, State
from app import augur
from flask_login import current_user
from cache_manager.cache_manager import CacheManager as cm
import cache_manager.cache_facade as cf
from queries.issues_query import issues_query as iq
from queries.commits_query import commits_query as cq
from queries.contributors_query import contributors_query as cnq
from queries.prs_query import prs_query as prq
from queries.affiliation_query import affiliation_query as aq
from queries.pr_assignee_query import pr_assignee_query as praq
from queries.issue_assignee_query import issue_assignee_query as iaq
from queries.user_groups_query import user_groups_query as ugq
from queries.pr_response_query import pr_response_query as prr

# from queries.cntrb_per_file_query import cntrb_per_file_query as cpfq - codebase page disabled
# from queries.repo_files_query import repo_files_query as rfq - codebase page disabled
# from queries.pr_files_query import pr_file_query as prfq - codebase page disabled
from queries.repo_languages_query import repo_languages_query as rlq
from queries.package_version_query import package_version_query as pvq
from queries.repo_releases_query import repo_releases_query as rrq
from queries.ossf_score_query import ossf_score_query as osq
from queries.repo_info_query import repo_info_query as riq
import redis
import flask


# list of queries to be run
# QUERIES = [iq, cq, cnq, prq, aq, iaq, praq, prr, cpfq, rfq, prfq, rlq, pvq, rrq, osq, riq] - codebase page disabled
QUERIES = [iq, cq, cnq, prq, aq, iaq, praq, prr, rlq, pvq, rrq, osq, riq]


# check if login has been enabled in config
login_enabled = os.getenv("AUGUR_LOGIN_ENABLED", "False") == "True"


@callback(
    [Output("user-group-loading-signal", "data")],
    [Input("url", "href"), Input("refresh-button", "n_clicks")],
)
def kick_off_group_collection(url, n_clicks):
    """Schedules a Celery task to collect user groups.
    Sends a message via localStorage that will kick off a background callback
    which waits for the Celery task to finish.

    if refresh-groups clicked, forces group reload.

    Args:
        url (str): browser page URL
        n_clicks (_type_): number 'refresh_groups' button has been clicked.

    Returns:
        int: ID of Celery task that has started for group collection.
    """
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        users_cache = redis.StrictRedis(
            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", ""),
        )
        try:
            users_cache.ping()
        except redis.exceptions.ConnectionError:
            logging.error("GROUP-COLLECTION: Could not connect to users-cache.")
            return dash.no_update

        # TODO: check how old groups are. If they're pretty old (threshold tbd) then requery

        # check if groups are not already cached, or if the refresh-button was pressed
        if not users_cache.exists(f"{user_id}_groups") or (dash.ctx.triggered_id == "refresh-button"):
            # kick off celery task to collect groups
            # on query worker queue,
            return [ugq.apply_async(args=[user_id], queue="data").id]
        else:
            return dash.no_update
    else:
        # user anonymous
        return dash.no_update


@callback(
    [
        Output("nav-login-container", "children"),
        Output("login-popover", "is_open"),
        Output("refresh-button", "disabled"),
        Output("logout-button", "disabled"),
        Output("manage-group-button", "disabled"),
    ],
    Input("url", "href"),
)
def login_username_button(url):
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

    navlink = [
        dbc.NavLink(
            "Augur log in/sign up",
            href="/login/",
            id="login-navlink",
            active=True,
            # communicating with the underlying Flask server
            external_link=True,
        ),
    ]

    buttons_disabled = True
    login_succeeded = True

    if current_user:
        if current_user.is_authenticated:
            logging.warning(f"LOGINBUTTON: USER LOGGED IN {current_user}")
            # TODO: implement more permanent interface
            users_cache = redis.StrictRedis(
                host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
                port=6379,
                password=os.getenv("REDIS_PASSWORD", ""),
            )
            try:
                users_cache.ping()
            except redis.exceptions.ConnectionError:
                logging.error("USERNAME: Could not connect to users-cache.")
                return dash.no_update

            user_id = current_user.get_id()
            user_info = json.loads(users_cache.get(user_id))

            navlink = [
                dbc.NavItem(
                    dbc.NavLink(
                        f"{user_info['username']}",
                        href=augur.user_account_endpoint,
                        id="login-navlink",
                        disabled=True,
                    ),
                ),
            ]
            buttons_disabled = False

    return (
        navlink,
        not login_succeeded,
        buttons_disabled,
        buttons_disabled,
        buttons_disabled,
    )


@callback(
    [Output("projects", "data")],
    [Input("projects", "searchValue")],
    [State("projects", "value"), State("cached-options", "data")],
)
def dynamic_multiselect_options(user_in: str, selections, cached_options):
    """
    Enhanced search using fuzzy matching and client-side cache with server fallback.

    Args:
        user_in: User's search input
        selections: Currently selected values
        cached_options: All available options from client-side cache
    """
    if not user_in:
        return dash.no_update

    try:
        start_time = time.time()
        logging.info(f"Search query: '{user_in}'")

        # Start with cached options if available
        if cached_options:
            logging.info(f"Using client-side cache with {len(cached_options)} options")
            options = cached_options
        else:
            logging.info("Client-side cache empty, fetching from server")
            options = augur.get_multiselect_options().copy()
            logging.info(f"Fetched {len(options)} options from server")
            if current_user.is_authenticated:
                try:
                    users_cache = redis.StrictRedis(
                        host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
                        port=6379,
                        password=os.getenv("REDIS_PASSWORD", ""),
                        decode_responses=True,
                    )
                    users_cache.ping()
                    if users_cache.exists(f"{current_user.get_id()}_group_options"):
                        user_options = json.loads(users_cache.get(f"{current_user.get_id()}_group_options"))
                        options = options + user_options
                        logging.info(f"Added {len(user_options)} user options from Redis")
                except redis.exceptions.ConnectionError as e:
                    logging.error(f"MULTISELECT: Could not connect to users-cache. Error: {str(e)}")

        if selections is None:
            selections = []

        # Remove prefixes from the search query if present
        search_query = user_in
        prefix_type = None

        if search_query.lower().startswith("repo:"):
            search_query = search_query[5:].strip()
            prefix_type = "repo"
            logging.info(f"Repo prefix detected, searching for: '{search_query}'")
        elif search_query.lower().startswith("org:"):
            search_query = search_query[4:].strip()
            prefix_type = "org"
            logging.info(f"Org prefix detected, searching for: '{search_query}'")

        # Perform fuzzy search with the refined query
        from .search_utils import fuzzy_search

        matched_options = fuzzy_search(search_query, options, threshold=0.2)
        logging.info(f"Fuzzy search found {len(matched_options)} matches in cache")

        # ENSURE EXACT ORG MATCHES: If searching for an org name, make sure it's included
        # This handles cases where fuzzy search limits might exclude exact org matches
        if len(search_query) >= 3:  # Only for meaningful queries
            exact_org_matches = []

            # Check for org matches in the FULL server dataset, not just cache
            # because orgs might not be in the limited cache
            try:
                server_options = augur.get_multiselect_options().copy()
                if current_user.is_authenticated:
                    try:
                        users_cache = redis.StrictRedis(
                            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
                            port=6379,
                            password=os.getenv("REDIS_PASSWORD", ""),
                            decode_responses=True,
                        )
                        users_cache.ping()
                        if users_cache.exists(f"{current_user.get_id()}_group_options"):
                            user_options = json.loads(users_cache.get(f"{current_user.get_id()}_group_options"))
                            server_options = server_options + user_options
                    except redis.exceptions.ConnectionError as e:
                        logging.error(f"ORG CHECK: Could not connect to users-cache. Error: {str(e)}")

                for opt in server_options:
                    if isinstance(opt.get("value"), str):  # It's an org
                        org_label = opt["label"].lower()
                        if (
                            search_query.lower() == org_label
                            or search_query.lower() in org_label
                            or org_label.startswith(search_query.lower())
                        ):
                            # Check if this org is already in matched_options
                            if not any(existing["value"] == opt["value"] for existing in matched_options):
                                exact_org_matches.append(opt)

            except Exception as e:
                logging.error(f"ORG CHECK: Failed to fetch server options: {str(e)}")

            # Add exact org matches to the beginning
            if exact_org_matches:
                matched_options = exact_org_matches + matched_options
                logging.info(f"Added {len(exact_org_matches)} exact org matches from server")

        # FALLBACK MECHANISM: If we have very few matches and we were using cache,
        # search the full server dataset
        use_server_fallback = False
        if cached_options and len(matched_options) < 5 and len(search_query) >= 3:
            logging.info("Few matches found in cache, falling back to server search")
            try:
                server_options = augur.get_multiselect_options().copy()
                if current_user.is_authenticated:
                    try:
                        users_cache = redis.StrictRedis(
                            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
                            port=6379,
                            password=os.getenv("REDIS_PASSWORD", ""),
                            decode_responses=True,
                        )
                        users_cache.ping()
                        if users_cache.exists(f"{current_user.get_id()}_group_options"):
                            user_options = json.loads(users_cache.get(f"{current_user.get_id()}_group_options"))
                            server_options = server_options + user_options
                    except redis.exceptions.ConnectionError as e:
                        logging.error(f"FALLBACK: Could not connect to users-cache. Error: {str(e)}")

                server_matches = fuzzy_search(search_query, server_options, threshold=0.2)
                logging.info(f"Server fallback found {len(server_matches)} matches")

                # Combine cache and server results, prioritizing cache matches
                seen_values = set(opt["value"] for opt in matched_options)
                for server_match in server_matches:
                    if server_match["value"] not in seen_values:
                        matched_options.append(server_match)
                        seen_values.add(server_match["value"])

                use_server_fallback = True
                logging.info(f"Combined results: {len(matched_options)} total matches")

            except Exception as e:
                logging.error(f"Server fallback failed: {str(e)}")

        # Filter by prefix type if specified
        if prefix_type == "repo":
            matched_options = [opt for opt in matched_options if isinstance(opt["value"], int)]
            logging.info(f"Filtered to {len(matched_options)} repos")
        elif prefix_type == "org":
            matched_options = [opt for opt in matched_options if isinstance(opt["value"], str)]
            logging.info(f"Filtered to {len(matched_options)} orgs")

        # Format options with prefixes based on their type
        formatted_opts = []
        seen_values = set()  # Track seen values to prevent duplicates

        for opt in matched_options:
            # Skip duplicates (based on value)
            if opt["value"] in seen_values:
                continue

            seen_values.add(opt["value"])
            formatted_opt = opt.copy()
            if isinstance(opt["value"], str):
                # It's an org
                formatted_opt["label"] = f"org: {opt['label']}"
            else:
                # It's a repo
                formatted_opt["label"] = f"repo: {opt['label']}"
            formatted_opts.append(formatted_opt)

        # Simple reordering: put organizations first, then repositories
        orgs_first = [opt for opt in formatted_opts if isinstance(opt["value"], str)]
        repos_after = [opt for opt in formatted_opts if isinstance(opt["value"], int)]
        formatted_opts = orgs_first + repos_after

        # Always include the previous selections
        # Format selected options with prefixes
        selected_options = []

        # First check if selections are in our current options (cache + any server fallback)
        current_selection_values = set(
            opt["value"] for opt in (cached_options or []) + (matched_options if use_server_fallback else [])
        )
        missing_selections = [v for v in selections if v not in current_selection_values]

        # If any selections aren't in our current options, fetch them from the server
        if missing_selections:
            logging.info(f"Fetching {len(missing_selections)} missing selections from server")
            all_options = augur.get_multiselect_options().copy()
            for v in selections:
                matched_opts = [opt for opt in all_options if opt["value"] == v]
                if matched_opts:
                    formatted_v = matched_opts[0].copy()
                    if isinstance(v, str):
                        # It's an org
                        formatted_v["label"] = f"org: {formatted_v['label']}"
                    else:
                        # It's a repo
                        formatted_v["label"] = f"repo: {formatted_v['label']}"
                    selected_options.append(formatted_v)
        else:
            # All selections are in our current options
            all_current_options = (cached_options or []) + matched_options
            for v in selections:
                for opt in all_current_options:
                    if opt["value"] == v:
                        formatted_v = opt.copy()
                        if isinstance(v, str):
                            # It's an org
                            formatted_v["label"] = f"org: {opt['label']}"
                        else:
                            # It's a repo
                            formatted_v["label"] = f"repo: {opt['label']}"
                        selected_options.append(formatted_v)
                        break

        # Combine results, limiting to 100 items but always including selections
        # ENSURE ORGS ARE ALWAYS INCLUDED: Separate orgs and repos, then combine smartly
        orgs_in_results = [opt for opt in formatted_opts if isinstance(opt["value"], str)]
        repos_in_results = [opt for opt in formatted_opts if isinstance(opt["value"], int)]

        if len(formatted_opts) < 100:
            result = formatted_opts
        else:
            # Always include all orgs (there are usually very few)
            # Then fill remaining slots with repos
            remaining_slots = 100 - len(orgs_in_results)
            if remaining_slots > 0:
                result = orgs_in_results + repos_in_results[:remaining_slots]
            else:
                # Edge case: more than 100 orgs (very unlikely)
                result = orgs_in_results[:100]

        # Add selected options that aren't already in the results
        selected_values = [opt["value"] for opt in result]
        for opt in selected_options:
            if opt["value"] not in selected_values:
                result.append(opt)

        end_time = time.time()
        logging.info(f"Search completed in {end_time - start_time:.2f} seconds")
        logging.info(f"Returning {len(result)} options to dropdown (fallback used: {use_server_fallback})")

        return [result]

    except Exception as e:
        logging.error(f"Error in dynamic_multiselect_options: {str(e)}")
        # Return at least the current selections as a fallback
        if selections:
            default_options = []
            try:
                # Try to get the labels for the current selections
                options = augur.get_multiselect_options()
                for v in options:
                    if v["value"] in selections:
                        formatted_v = v.copy()
                        if isinstance(v["value"], str):
                            formatted_v["label"] = f"org: {v['label']}"
                        else:
                            formatted_v["label"] = f"repo: {v['label']}"
                        default_options.append(formatted_v)
            except:
                # If that fails, just return the raw selection values
                default_options = [{"value": v, "label": f"ID: {v}"} for v in selections]

            return [default_options]

        return dash.no_update


# callback for repo selections to feed into visualization call backs
@callback(
    [Output("results-output-container", "children"), Output("repo-choices", "data")],
    [
        Input("search", "n_clicks"),
        State("projects", "value"),
    ],
)
def multiselect_values_to_repo_ids(n_clicks, user_vals):
    if not user_vals:
        logging.warning("NOTHING SELECTED IN SEARCH BAR")
        raise dash.exceptions.PreventUpdate

    # individual repo numbers
    repos = [r for r in user_vals if isinstance(r, int)]
    logging.warning(f"REPOS: {repos}")

    # names of augur groups or orgs
    names = [n for n in user_vals if isinstance(n, str)]

    org_repos = [augur.org_to_repos(o) for o in names if augur.is_org(o)]
    # flatten list repo_ids in orgs to 1D
    org_repos = [v for l in org_repos for v in l]
    logging.warning(f"ORG_REPOS: {org_repos}")

    user_groups = []
    if current_user.is_authenticated:
        logging.warning(f"LOGINBUTTON: USER LOGGED IN {current_user}")
        # TODO: implement more permanent interface
        users_cache = redis.StrictRedis(
            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", ""),
            decode_responses=True,
        )
        try:
            users_cache.ping()
        except redis.exceptions.ConnectionError:
            logging.error("SEARCH-BUTTON: Could not connect to users-cache.")
            return dash.no_update

        try:
            if users_cache.exists(f"{current_user.get_id()}_groups"):
                user_groups = json.loads(users_cache.get(f"{current_user.get_id()}_groups"))
                logging.warning(f"USERS Groups: {type(user_groups)}, {user_groups}")
        except redis.exceptions.ConnectionError:
            logging.error("Searchbar: couldn't connect to Redis for user group options.")

    group_repos = [user_groups[g] for g in names if not augur.is_org(g)]
    # flatten list repo_ids in orgs to 1D
    group_repos = [v for l in group_repos for v in l]
    logging.warning(f"GROUP_REPOS: {group_repos}")

    # only unique repo ids
    all_repo_ids = list(set().union(*[repos, org_repos, group_repos]))
    logging.warning(f"SELECTED_REPOS: {all_repo_ids}")

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
    [Output("repo-list-alert", "is_open"), Output("repo-list-alert", "children")],
    [Input("repo-list-button", "n_clicks")],
    [State("help-alert", "is_open"), State("repo-choices", "data")],
)
def show_help_alert(n_clicks, openness, repo_ids):
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
    print(repo_ids)
    url_list = [augur.repo_id_to_git(i) for i in repo_ids]

    if n_clicks == 0:
        return dash.no_update, str(url_list)
    # switch the openness parameter, allows button to also
    # dismiss the Alert.
    return not openness, str(url_list)


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
        logging.warning([(j.name, j.status) for j in jobs])

        # jobs are either all ready
        if all(j.successful() for j in jobs):
            logging.warning([(j.name, j.status) for j in jobs])
            jobs = [j.forget() for j in jobs]
            return "Data Ready", "#b5b683"

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
    instance for input Repos; caches results in Postgres.

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
        not_ready = cf.get_uncached(f.__name__, repos)
        if len(not_ready) == 0:
            logging.warning(f"{f.__name__} - NO DISPATCH - ALL REPOS IN CACHE")
            continue

        # add job to queue
        j = f.apply_async(args=[not_ready], queue="data")

        # add job promise to local promise list
        jobs.append(j)

    return [j.id for j in jobs]


# Add a cache initialization callback that runs on page load
@callback(
    Output("cached-options", "data"),
    Input("cache-init-trigger", "children"),  # Dummy input to trigger on page load
    prevent_initial_call=False,
)
def initialize_cache(_):
    """
    Initialize the client-side cache with all options.
    This runs once when the page loads.
    """
    try:
        logging.info("Initializing client-side options cache")
        options = augur.get_multiselect_options().copy()
        logging.info(f"Retrieved {len(options)} options from augur")

        if current_user.is_authenticated:
            try:
                users_cache = redis.StrictRedis(
                    host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
                    port=6379,
                    password=os.getenv("REDIS_PASSWORD", ""),
                    decode_responses=True,
                )
                users_cache.ping()

                if users_cache.exists(f"{current_user.get_id()}_group_options"):
                    user_options = json.loads(users_cache.get(f"{current_user.get_id()}_group_options"))
                    options = options + user_options
                    logging.info(f"Added {len(user_options)} user-specific options from Redis")
            except redis.exceptions.ConnectionError as e:
                logging.error(f"CACHE INIT: Could not connect to users-cache. Error: {str(e)}")

        # Get configuration from environment variables with defaults
        sort_method = os.getenv("EIGHTKNOT_SEARCHBAR_OPTS_SORT", "shortest").lower()
        max_total_results = int(os.getenv("EIGHTKNOT_SEARCHBAR_OPTS_MAX_RESULTS", "2000"))
        max_repos = int(os.getenv("EIGHTKNOT_SEARCHBAR_OPTS_MAX_REPOS", "1500"))

        # Sort options based on configuration
        if sort_method == "shortest":
            # Sort by label length to prioritize shorter names (default)
            options.sort(key=lambda x: len(x.get("label", "")))
        elif sort_method == "longest":
            # Sort by label length in reverse to prioritize longer names
            options.sort(key=lambda x: -len(x.get("label", "")))
        elif sort_method == "alphabetical":
            # Sort alphabetically
            options.sort(key=lambda x: x.get("label", "").lower())

        # For repos, keep the configured maximum number
        repos = [opt for opt in options if isinstance(opt.get("value"), int)][:max_repos]

        # For orgs, keep all (there are usually only a few hundred)
        orgs = [opt for opt in options if isinstance(opt.get("value"), str)]

        # Combine and prepare for storage, limiting to max_total_results
        minimal_options = (repos + orgs)[:max_total_results]

        logging.info(f"Cache initialized with {len(minimal_options)} total options (reduced from {len(options)})")
        return minimal_options
    except Exception as e:
        logging.error(f"Cache initialization failed: {str(e)}")
        # Return an empty list as a fallback to prevent complete failure
        return []


# Add search status indicator callbacks
@callback(
    [Output("search-status", "children"), Output("search-status", "className"), Output("search-status", "style")],
    [Input("projects", "searchValue")],
    prevent_initial_call=True,
)
def update_search_status(search_value):
    """Update the search status indicator when a search is performed."""
    if search_value and len(search_value) > 0:
        return ["Searching...", "search-status-indicator searching", {"display": "block"}]
    return ["", "search-status-indicator", {"display": "none"}]


# Callback to hide the search status when results are loaded
@callback(
    [Output("search-status", "style", allow_duplicate=True)], [Input("projects", "data")], prevent_initial_call=True
)
def hide_search_status_when_loaded(_):
    """Hide the search status indicator when results are loaded."""
    return [{"display": "none"}]
