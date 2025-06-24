from datetime import datetime, timedelta
import re
import os
import time
import logging
import json
from celery.result import AsyncResult
import dash_bootstrap_components as dbc
import dash
from dash import callback, html
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
def show_repo_list_alert(n_clicks, openness, repo_ids):
    """Sets the 'open' state of a repo list alert
    showing all selected repository URLs.
    Args:
        n_clicks (int): number of times 'repo list' button clicked.
        openness (boolean): whether help alert is currently open.
        repo_ids (list): list of selected repository IDs.
    Returns:
        dash.no_update | boolean: whether the repo list alert should be open.
    """
    if repo_ids:
        url_list = [augur.repo_id_to_git(i) for i in repo_ids]
    else:
        url_list = []

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
    
    # If no repos are selected, don't run any queries
    if not repos or len(repos) == 0:
        logging.info("RUN_QUERIES: No repositories selected, skipping query execution")
        return []

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


# Callback to set default tag on page load
@callback(
    Output("selected-tags", "data", allow_duplicate=True),
    [Input("cached-options", "data")],
    prevent_initial_call="initial_duplicate"
)
def set_default_tag_on_load(cached_options):
    """
    Set the default tag when the page loads, using the same logic as the old system
    """
    if not cached_options:
        # If cache isn't ready yet, don't update - let it trigger again when cache is ready
        logging.info("Default tag callback: cached_options not ready yet")
        return dash.no_update
    
    try:
        # Use the same logic as augur.initial_multiselect_option()
        initial_option = augur.initial_multiselect_option()
        if initial_option and initial_option["value"] != -1:  # -1 is the fallback
            logging.info(f"Setting default tag: {initial_option['value']}")
            return [initial_option["value"]]
        else:
            # Fallback to first option if available
            if cached_options and len(cached_options) > 0:
                logging.info(f"Setting fallback default tag: {cached_options[0]['value']}")
                return [cached_options[0]["value"]]
    except Exception as e:
        logging.error(f"Error setting default tag: {str(e)}")
    
    logging.info("No default tag set")
    return []


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
                logging.info("Successfully connected to Redis")

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


# Dash callback for sidebar toggle
@dash.callback(
    [
        Output("sidebar-card", "style"),
        Output("sidebar-full-content", "style"),
        # Output("home-text", "style"),
        Output("repo-overview-text", "style"),
        Output("contributions-text", "style"),
        Output("contributors-text", "style"),
        Output("affiliation-text", "style"),
        Output("chaoss-text", "style"),
        Output("codebase-text", "style"),
        Output("main-card", "style"),
        Output("sidebar-toggle-icon", "className"),
        Output("sidebar-collapsed", "data"),
        # Contributors dropdown outputs to close dropdown when sidebar collapses
        Output("contributors-dropdown-content", "style", allow_duplicate=True),
        Output("contributors-dropdown-icon", "className", allow_duplicate=True),
        Output("contributors-dropdown-open", "data", allow_duplicate=True),
        Output("contributors-dropdown-wrapper", "className", allow_duplicate=True),
    ],
    [Input("sidebar-toggle-btn", "n_clicks")],
    [State("sidebar-collapsed", "data")],
    prevent_initial_call=True,
)
def toggle_sidebar(n, collapsed):
    if not n:
        raise dash.exceptions.PreventUpdate
    collapsed = not collapsed
    
    # Text visibility style
    text_style = {"display": "none"} if collapsed else {"display": "inline"}
    
    # Full content visibility style
    full_content_style = {"display": "none"} if collapsed else {"display": "block"}
    
    sidebar_style = {
        "borderRadius": "14px 0 0 14px",
        "height": "95vh",
        "width": "80px" if collapsed else "340px",
        "background": "#1D1D1D",  # FIXED: match static style
        "color": "#fff",
        "padding": "32px 12px 32px 12px" if collapsed else "32px 18px 32px 18px",
        "boxShadow": "none",  # Remove shadow from sidebar card
        "borderRight": "1px solid #404040",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",
        "margin": "0px 0 20px 10px",  # always 0 top margin to keep content flush with navbar
        "zIndex": 2,
        "transition": "width 0.3s cubic-bezier(.4,2,.6,1)",
        "overflow": "hidden",
    }
    main_style = {
        "borderRadius": "0 14px 14px 0",
        "padding": "0px 40px 40px 40px",  # always 0 top padding
        "margin": "0px 10px 20px 0",      # always 0 top margin
        "width": f"calc(99vw - {'80px' if collapsed else '340px'})",
        "maxWidth": f"calc(100vw - {'80px' if collapsed else '340px'})",
        "boxShadow": "none",  # Remove shadow from main card
        "background": "#1D1D1D",  # FIXED: match static style
        "height": "95vh",
        "overflowY": "auto",
        "overflowX": "hidden",
        "display": "flex",
        "flexDirection": "column",
        "transition": "margin-left 0.3s cubic-bezier(.4,2,.6,1)",
        "marginLeft": "0",
    }
    icon = "fas fa-chevron-right" if collapsed else "fas fa-chevron-left"
    
    # When sidebar is collapsed, always close the contributors dropdown
    if collapsed:
        dropdown_content_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
        dropdown_icon_class = "bi bi-chevron-down"
        dropdown_open = False
        dropdown_wrapper_class = ""
    else:
        # When sidebar is expanded, don't change dropdown state - use dash.no_update
        dropdown_content_style = dash.no_update
        dropdown_icon_class = dash.no_update
        dropdown_open = dash.no_update
        dropdown_wrapper_class = dash.no_update
    
    return (
        sidebar_style, 
        full_content_style, 
        text_style, text_style, text_style, text_style, text_style, text_style,
        main_style, 
        icon, 
        collapsed,
        dropdown_content_style,
        dropdown_icon_class,
        dropdown_open,
        dropdown_wrapper_class
    )

# Callback for contributors dropdown
@dash.callback(
    [
        Output("contributors-dropdown-content", "style"),
        Output("contributors-dropdown-icon", "className"),
        Output("contributors-dropdown-open", "data"),
        Output("sidebar-collapsed", "data", allow_duplicate=True),
        Output("contributors-dropdown-wrapper", "className"),
        Output("sidebar-card", "style", allow_duplicate=True),
        Output("sidebar-full-content", "style", allow_duplicate=True),
        Output("repo-overview-text", "style", allow_duplicate=True),
        Output("contributions-text", "style", allow_duplicate=True),
        Output("contributors-text", "style", allow_duplicate=True),
        Output("affiliation-text", "style", allow_duplicate=True),
        Output("chaoss-text", "style", allow_duplicate=True),
        Output("codebase-text", "style", allow_duplicate=True),
        Output("main-card", "style", allow_duplicate=True),
        Output("sidebar-toggle-icon", "className", allow_duplicate=True),
    ],
    [
        Input("contributors-dropdown-toggle", "n_clicks"),
        Input("repo-overview-navlink", "n_clicks"),
        Input("contributions-navlink", "n_clicks"), 
        Input("affiliation-navlink", "n_clicks"),
        Input("chaoss-navlink", "n_clicks"),
        Input("codebase-navlink", "n_clicks"),
    ],
    [
        State("contributors-dropdown-open", "data"),
        State("sidebar-collapsed", "data"),
    ],
    prevent_initial_call=True,
)
def toggle_contributors_dropdown(dropdown_clicks, repo_clicks, contrib_clicks, aff_clicks, chaoss_clicks, code_clicks, dropdown_open, sidebar_collapsed):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # If any other navlink was clicked, close dropdown but don't change sidebar
    if trigger_id in ["repo-overview-navlink", "contributions-navlink", "affiliation-navlink", "chaoss-navlink", "codebase-navlink"]:
        dropdown_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
        icon_class = "bi bi-chevron-down"
        wrapper_class = ""
        # Return current sidebar state unchanged - use dash.no_update for all sidebar-related outputs
        return dropdown_style, icon_class, False, sidebar_collapsed, wrapper_class, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # If contributors dropdown toggle was clicked
    if trigger_id == "contributors-dropdown-toggle":
        # ALWAYS expand the sidebar when contributors dropdown is clicked
        dropdown_open = not dropdown_open
        
        if dropdown_open:
            dropdown_style = {"display": "block", "paddingTop": "4px", "borderRadius": "0 0 8px 8px"}
            wrapper_class = "dropdown-open"
        else:
            dropdown_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
            wrapper_class = ""
        
        icon_class = "bi bi-chevron-up" if dropdown_open else "bi bi-chevron-down"
        
        # Force sidebar to expanded state (like circular button click)
        collapsed = False  # Always expanded
        
        # Text visibility style (expanded)
        text_style = {"display": "inline"}
        
        # Contributors dropdown icon style (expanded)
        dropdown_icon_style = {
            "marginLeft": "auto",
            "fontSize": "12px",
            "color": "#B0B0B0",
            "display": "inline"
        }
        
        # Full content visibility style (expanded)
        full_content_style = {"display": "block"}
        
        # Sidebar style (expanded)
        sidebar_style = {
            "borderRadius": "14px 0 0 14px",
            "height": "95vh",
            "width": "340px",
            "background": "#1D1D1D",
            "color": "#fff",
            "padding": "32px 18px 32px 18px",
            "boxShadow": "none",
            "borderRight": "1px solid #404040",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flex-start",
            "margin": "0px 0 20px 10px",
            "zIndex": 2,
            "transition": "width 0.3s cubic-bezier(.4,2,.6,1)",
            "overflow": "hidden",
        }
        
        # Main card style (expanded)
        main_style = {
            "borderRadius": "0 14px 14px 0",
            "padding": "0px 40px 40px 40px",
            "margin": "0px 10px 20px 0",
            "width": "calc(99vw - 340px)",
            "maxWidth": "calc(100vw - 340px)",
            "boxShadow": "none",
            "background": "#1D1D1D",
            "height": "95vh",
            "overflowY": "auto",
            "overflowX": "hidden",
            "display": "flex",
            "flexDirection": "column",
            "transition": "margin-left 0.3s cubic-bezier(.4,2,.6,1)",
            "marginLeft": "0",
        }
        
        # Toggle icon (expanded)
        toggle_icon = "fas fa-chevron-left"
        
        return dropdown_style, icon_class, dropdown_open, collapsed, wrapper_class, sidebar_style, full_content_style, text_style, text_style, text_style, text_style, text_style, text_style, main_style, toggle_icon
    
    raise dash.exceptions.PreventUpdate

# Callback to control search dropdown popup visibility
@callback(
    Output("search-dropdown-popup", "style"),
    [Input("my-input", "value")],
    [State("search-dropdown-popup", "style")]
)
def toggle_search_popup(input_value, current_style):
    """
    Show/hide the search dropdown popup based on input content.
    The dropdown should be hidden by default and show when user focuses/types.
    """
    # Start with the current style or default
    new_style = current_style.copy() if current_style else {
        "position": "absolute",
        "top": "100%",
        "left": "0",
        "right": "0",
        "zIndex": "1000",
        "maxHeight": "300px",
        "overflowY": "auto",
        "marginTop": "2px",
        "display": "none"  # Hidden by default
    }
    
    # Show dropdown when user starts typing, keep hidden when empty
    # The clientside callback will handle showing it on focus and hiding on click outside
    if input_value:
        new_style["display"] = "block"
    else:
        new_style["display"] = "none"
    
    return new_style


# Callback to update search results based on input
@callback(
    Output("search-results-list", "children"),
    [Input("my-input", "value")],
    [State("cached-options", "data")],
    prevent_initial_call=True
)
def update_search_results(search_value, cached_options):
    """
    Update search results based on user input using the existing search logic
    """
    if not search_value or not cached_options:
        return [
            html.Div(
                "Start typing to search for repositories and organizations...",
                style={"padding": "12px", "color": "#B0B0B0", "textAlign": "center"}
            )
        ]
    
    try:
        # Use the same search logic as the original multiselect
        from .search_utils import fuzzy_search
        
        # Remove prefixes from the search query if present
        search_query = search_value
        prefix_type = None

        if search_query.lower().startswith("repo:"):
            search_query = search_query[5:].strip()
            prefix_type = "repo"
        elif search_query.lower().startswith("org:"):
            search_query = search_query[4:].strip()
            prefix_type = "org"

        # Perform fuzzy search
        matched_options = fuzzy_search(search_query, cached_options, threshold=0.2)
        
        # Filter by prefix type if specified
        if prefix_type == "repo":
            matched_options = [opt for opt in matched_options if isinstance(opt["value"], int)]
        elif prefix_type == "org":
            matched_options = [opt for opt in matched_options if isinstance(opt["value"], str)]
        
        # Limit results for performance
        matched_options = matched_options[:20]
        
        if not matched_options:
            return [
                html.Div(
                    "No matches found. Try adjusting your search terms.",
                    style={"padding": "12px", "color": "#B0B0B0", "textAlign": "center"}
                )
            ]
        
        # Create clickable result items
        result_items = []
        for opt in matched_options:
            is_org = isinstance(opt["value"], str)
            icon = "🏢" if is_org else "📁"
            prefix = "org:" if is_org else "repo:"
            
            result_item = html.Div(
                [
                    html.Span(f"{icon} ", style={"marginRight": "8px"}),
                    html.Span(f"{prefix} {opt['label']}", style={"fontWeight": "500"}),
                ],
                id={"type": "search-result-item", "index": opt["value"]},
                style={
                    "padding": "8px 12px",
                    "cursor": "pointer",
                    "borderRadius": "4px",
                    "marginBottom": "2px",
                    "transition": "background-color 0.2s ease"
                },
                className="search-result-item"
            )
            result_items.append(result_item)
        
        return result_items
        
    except Exception as e:
        logging.error(f"Error in update_search_results: {str(e)}")
        return [
            html.Div(
                "Error loading search results. Please try again.",
                style={"padding": "12px", "color": "#ff6b6b", "textAlign": "center"}
            )
        ]


# Callback to handle clicking on search results and add tags
@callback(
    [Output("selected-tags", "data"), Output("my-input", "value")],
    [Input({"type": "search-result-item", "index": dash.dependencies.ALL}, "n_clicks")],
    [State("selected-tags", "data"), State("my-input", "value"), State("cached-options", "data")],
    prevent_initial_call=True
)
def add_selected_tag(n_clicks_list, selected_tags, input_value, cached_options):
    """
    Add clicked search result to selected tags
    """
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return dash.no_update, dash.no_update
    
    # Find which item was clicked
    triggered_id = ctx.triggered[0]["prop_id"]
    import json
    clicked_item = json.loads(triggered_id.split('.')[0])
    selected_value = clicked_item["index"]
    
    # Add to selected tags if not already present
    if selected_tags is None:
        selected_tags = []
    
    if selected_value not in selected_tags:
        selected_tags.append(selected_value)
    
    # Clear the input and return updated tags
    return selected_tags, ""


# Callback to display selected tags with proper labels
@callback(
    Output("selected-tags-container", "children"),
    [Input("selected-tags", "data")],
    [State("cached-options", "data")],
    prevent_initial_call=False  # Allow initial call to display default tags
)
def display_selected_tags(selected_tags, cached_options):
    """
    Display selected tags as removable chips with proper labels (inline style)
    """
    if not selected_tags:
        return []
    
    # If cached_options not ready yet, return placeholder tags with just the values
    if not cached_options:
        tag_elements = []
        for tag_value in selected_tags:
            display_label = f"Loading... {tag_value}"
            tag_element = html.Div(
                [
                    html.Span(display_label, style={"marginRight": "4px"}),
                    html.Button(
                        "×",
                        id={"type": "remove-tag", "index": tag_value},
                        className="tag-remove-btn",
                        style={
                            "background": "none",
                            "border": "none",
                            "color": "white",
                            "cursor": "pointer",
                            "fontSize": "16px",
                            "lineHeight": "1",
                            "padding": "0",
                            "width": "16px",
                            "height": "16px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "borderRadius": "50%"
                        }
                    )
                ],
                className="selected-tag",
                style={
                    "backgroundColor": "#119DFF",
                    "color": "white",
                    "padding": "4px 8px",
                    "borderRadius": "12px",
                    "fontSize": "14px",
                    "display": "inline-flex",
                    "alignItems": "center",
                    "gap": "6px"
                }
            )
            tag_elements.append(tag_element)
        return tag_elements
    
    tag_elements = []
    for tag_value in selected_tags:
        # Find the label for this value
        tag_label = str(tag_value)  # fallback
        for opt in cached_options:
            if opt["value"] == tag_value:
                is_org = isinstance(tag_value, str)
                prefix = "org:" if is_org else "repo:"
                tag_label = f"{prefix} {opt['label']}"
                break
        
        # Truncate long labels for inline display
        display_label = tag_label if len(tag_label) <= 25 else tag_label[:22] + "..."
        
        tag_element = html.Div(
            [
                html.Span(display_label, style={"marginRight": "4px"}),
                html.Button(
                    "×",
                    id={"type": "remove-tag", "index": tag_value},
                    className="tag-remove-btn",
                    style={
                        "background": "none",
                        "border": "none",
                        "color": "white",
                        "cursor": "pointer",
                        "fontSize": "16px",
                        "lineHeight": "1",
                        "padding": "0",
                        "width": "16px",
                        "height": "16px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "borderRadius": "50%"
                    }
                )
            ],
            className="selected-tag",
            style={
                "backgroundColor": "#119DFF",
                "color": "white",
                "padding": "4px 8px",
                "borderRadius": "12px",
                "fontSize": "14px",
                "display": "inline-flex",
                "alignItems": "center",
                "gap": "6px"
            }
        )
        tag_elements.append(tag_element)
    
    return tag_elements


# Callback to trigger initial search when default tag is set
@callback(
    Output("search", "n_clicks", allow_duplicate=True),
    [Input("selected-tags", "data")],
    [State("search", "n_clicks")],
    prevent_initial_call=True
)
def trigger_initial_search(selected_tags, current_clicks):
    """
    Trigger search automatically when default tag is first set on page load
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Only auto-trigger if this is the first time tags are set (likely the default tag)
    # and user hasn't clicked search yet
    if selected_tags and (current_clicks is None or current_clicks == 0):
        logging.info("Auto-triggering search for default tag")
        return 1  # Simulate one search button click
    
    return dash.no_update


# Updated callback for repo selections to work with the new tag system
@callback(
    [Output("results-output-container", "children"), Output("repo-choices", "data")],
    [
        Input("search", "n_clicks"),
        Input("my-input", "n_submit"),  # Trigger when user hits Enter in search input
    ],
    [State("selected-tags", "data")],  # Get current tags as state, don't trigger on change
    prevent_initial_call=False  # Allow initial call to fire with default tags
)
def multiselect_values_to_repo_ids(n_clicks, n_submit, selected_tags):
    # Allow triggering from either search button click or Enter key press
    if not selected_tags:
        logging.warning("NOTHING SELECTED IN SEARCH BAR")
        # Don't prevent update - let it run with empty list to show empty state
        return "", []

    # individual repo numbers
    repos = [r for r in selected_tags if isinstance(r, int)]
    logging.warning(f"REPOS: {repos}")

    # names of augur groups or orgs
    names = [n for n in selected_tags if isinstance(n, str)]

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


# Callback to handle removing tags
@callback(
    Output("selected-tags", "data", allow_duplicate=True),
    [Input({"type": "remove-tag", "index": dash.dependencies.ALL}, "n_clicks")],
    [State("selected-tags", "data")],
    prevent_initial_call=True
)
def remove_selected_tag(n_clicks_list, selected_tags):
    """
    Remove clicked tag from selected tags
    """
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return dash.no_update
    
    # Find which tag was clicked for removal
    triggered_id = ctx.triggered[0]["prop_id"]
    import json
    clicked_item = json.loads(triggered_id.split('.')[0])
    tag_to_remove = clicked_item["index"]
    
    # Remove from selected tags
    if selected_tags and tag_to_remove in selected_tags:
        selected_tags.remove(tag_to_remove)
    
    return selected_tags

# Callback to update placeholder text based on whether tags are present
@callback(
    Output("my-input", "placeholder"),
    [Input("selected-tags", "data")],
    prevent_initial_call=False  # Allow initial call to set proper placeholder
)
def update_placeholder(selected_tags):
    """
    Update placeholder text based on whether tags are selected
    """
    if selected_tags and len(selected_tags) > 0:
        return "Add more repos/organizations..."
    else:
        return "Search for repos/organizations..."


