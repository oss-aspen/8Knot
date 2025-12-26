from datetime import datetime, timedelta
import re
import os
import time
import logging
import json
import threading
from typing import Optional
from celery.result import AsyncResult
import dash_bootstrap_components as dbc
import dash
from dash import callback, html
from dash.dependencies import Input, Output, State, MATCH
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
from models import SearchItem
import redis
import flask
from .search_utils import fuzzy_search
from .search_utils import clean_repo_name
from .search_utils import get_adaptive_debounce_time
from .query_constants import (
    QUERY_STATUS_CACHED,
    PAGE_STATUS_IDLE,
    PAGE_STATUS_READY,
    PAGE_STATUS_FAILED,
    PAGE_STATUS_TIMEOUT,
    CURRENT_PAGE_POLL_INTERVAL,
    MAX_QUERY_WAIT_TIME,
    BADGE_TEXT_NO_DATA,
    BADGE_TEXT_ALL_READY,
    BADGE_TEXT_PAGE_READY,
    BADGE_TEXT_PAGE_FAILED,
    BADGE_TEXT_PAGE_TIMEOUT,
    BADGE_TEXT_DATA_READY,
    BADGE_TEXT_TIMEOUT_RETRY,
    BADGE_TEXT_DATA_INCOMPLETE,
    BADGE_COLOR_READY,
    BADGE_COLOR_LOADING,
    BADGE_COLOR_ERROR,
    BADGE_COLOR_WARNING,
    BADGE_COLOR_SECONDARY,
)
from .query_job_utils import (
    create_async_results_from_metadata,
    check_all_jobs_complete,
    wait_for_job_completion,
    forget_jobs,
)

# list of queries to be run
# QUERIES = [iq, cq, cnq, prq, aq, iaq, praq, prr, cpfq, rfq, prfq, rlq, pvq, rrq, osq, riq] - codebase page disabled
QUERIES = [iq, cq, cnq, prq, aq, iaq, praq, prr, rlq, pvq, rrq, osq, riq]

# Map pages to their required queries for priority loading
PAGE_QUERIES = {
    "/home": [cq, iq, prq],
    "/repo_overview": [rlq, pvq, rrq, osq, riq],
    "/contributions": [iq, cq, prq, iaq, praq, prr],
    "/contributors/behavior": [cq, cnq],
    "/contributors/contribution_types": [cq, cnq],
    "/affiliation": [aq, cq],
    "/chaoss": [cnq],
}


# Helper function to get query names for a page
def get_page_query_names(page_path):
    """Get list of query function names for a given page path."""
    queries = PAGE_QUERIES.get(page_path, [])
    return [q.__name__ for q in queries]


# check if login has been enabled in config
login_enabled = os.getenv("AUGUR_LOGIN_ENABLED", "False") == "True"


# Adaptive debounce state manager
class AdaptiveDebounceManager:
    """
    Manages adaptive debouncing for search queries.

    The component-level debounce (100ms) provides frequent check-ins.
    This manager applies adaptive debouncing based on query length:
    - Short queries (1-3 chars): Longer debounce (800-400ms) - user likely still typing
    - Medium queries (4-5 chars): Medium debounce (250ms) - user may be finishing
    - Long queries (6+ chars): Shorter debounce (150ms) - user likely finished

    Strategy: Track when each unique query was first seen. Only process queries
    that have been stable (unchanged) for the required adaptive debounce time.

    Note: Dash Mantine Components' debounce prop is static, so we implement
    adaptive debouncing in the callback logic rather than changing the component prop.
    """

    # Constants
    COMPONENT_DEBOUNCE_SECONDS = 0.1  # 100ms from component
    MIN_REPROCESS_INTERVAL_SECONDS = 0.1  # Don't reprocess same query within 100ms
    CLEANUP_AGE_SECONDS = 5.0  # Remove queries older than 5 seconds

    # Immediate processing thresholds (for detecting active typing)
    SIGNIFICANT_LENGTH_INCREASE = 3  # Process immediately if query is 3+ chars longer
    PREFIX_EXTENSION_THRESHOLD = 2  # Process immediately if prefix extension is 2+ chars longer

    def __init__(self):
        self._lock = threading.Lock()  # Thread safety for concurrent Dash callbacks
        self._query_first_seen: dict[str, float] = {}  # Map query -> first time seen
        self._last_processed_query: Optional[str] = None
        self._last_processed_time: float = 0.0
        self._last_results: list = []  # Store last results to return during debouncing (empty = no cache yet)
        self._has_processed_any_query: bool = False  # Track if we've ever processed a query

    def should_process_query(self, query: str) -> bool:
        """
        Determine if a query should be processed based on adaptive debounce logic.

        Thread-safe: Uses locking to prevent race conditions in multi-threaded Dash environments.
        Optimized with fast-path checks to minimize lock contention and reduce typing pauses.

        Performance optimizations:
        1. Fast-path lock-free check for duplicate queries (most common case)
        2. Pre-compute expensive operations outside lock
        3. Minimize time spent holding lock
        4. Defer logging until after lock release

        Args:
            query: The current search query

        Returns:
            True if query should be processed, False if it should be debounced
        """
        current_time = time.time()

        # FAST PATH: Lock-free check for same query reprocessing (most common case)
        # Read-only access to these vars is safe without lock (they're only written with lock held)
        if query == self._last_processed_query:
            if current_time - self._last_processed_time < self.MIN_REPROCESS_INTERVAL_SECONDS:
                return False  # Same query, too soon - no lock needed

        # PRE-COMPUTE: Do expensive operations BEFORE acquiring lock
        query_length = len(query)
        debounce_seconds = get_adaptive_debounce_time(query) / 1000.0
        effective_debounce = max(self.COMPONENT_DEBOUNCE_SECONDS, debounce_seconds)

        # Variables for deferred logging (to minimize lock duration)
        should_log = False
        log_message = ""

        # LOCK REQUIRED: For all state-mutating operations
        # Keep lock scope as small as possible
        with self._lock:
            # Re-check time in case it changed while waiting for lock
            if query == self._last_processed_query:
                if current_time - self._last_processed_time < self.MIN_REPROCESS_INTERVAL_SECONDS:
                    return False

            # Track when this query was first seen (reset timer if query changed)
            if query not in self._query_first_seen:
                self._query_first_seen[query] = current_time

            # IMPORTANT: If query is significantly longer than last processed, process immediately
            # This handles the case where user types quickly (e.g., "k" -> "kubernetes")
            # The user is actively building up the query, so we should process it
            if self._last_processed_query is not None:
                length_diff = query_length - len(self._last_processed_query)
                # If query is significantly longer OR is a prefix extension (user actively typing), process immediately
                is_prefix_extension = query.startswith(self._last_processed_query) and length_diff > 0
                if length_diff >= self.SIGNIFICANT_LENGTH_INCREASE or (
                    is_prefix_extension and length_diff >= self.PREFIX_EXTENSION_THRESHOLD
                ):
                    # Defer logging until after lock release
                    should_log = True
                    log_message = (
                        f"Query '{query[:50]}...' processed immediately (length increased by {length_diff} chars, "
                        f"user actively typing: '{self._last_processed_query}' -> '{query}', "
                        f"is_prefix={is_prefix_extension})"
                    )
                    self._last_processed_query = query
                    self._last_processed_time = current_time
                    self._cleanup_old_queries(current_time)

                    # Release lock before logging
                    result = True
                    # Lock will be released here
            else:
                result = None

            if result is None:  # Not early exit, continue normal flow
                # Check if query has been stable long enough
                query_stable_time = current_time - self._query_first_seen[query]

                if query_stable_time >= effective_debounce:
                    # Query is ready to process
                    self._last_processed_query = query
                    self._last_processed_time = current_time
                    self._cleanup_old_queries(current_time)

                    # Defer logging until after lock release
                    should_log = True
                    log_message = (
                        f"Query '{query[:50]}...' processed after {query_stable_time:.3f}s "
                        f"stable time (debounce: {debounce_seconds*1000:.0f}ms, "
                        f"length: {query_length})"
                    )
                    result = True
                else:
                    result = False

        # DEFERRED LOGGING: Log AFTER releasing lock to minimize lock duration
        if should_log:
            logging.info(log_message)

        return result

    def mark_query_processed(self, query: str) -> None:
        """
        Mark a query as processed without checking debounce time.
        Used when bypassing debounce (e.g., for first query with no cached results).

        Args:
            query: The query to mark as processed
        """
        with self._lock:
            current_time = time.time()
            self._last_processed_query = query
            self._last_processed_time = current_time
            # Ensure query is tracked
            if query not in self._query_first_seen:
                self._query_first_seen[query] = current_time
            self._cleanup_old_queries(current_time)

    def set_last_results(self, results: list) -> None:
        """
        Store the last results to return during debouncing.

        Args:
            results: The search results list (can be empty [] for zero matches)
        """
        with self._lock:
            # Store results even if empty - empty list is a valid search result
            self._last_results = results.copy() if results else []
            self._has_processed_any_query = True

    def get_last_results(self) -> list:
        """
        Get the last results to return during debouncing.

        Returns:
            The cached results list (empty list if no results cached yet or if previous search returned zero matches).
        """
        with self._lock:
            return self._last_results.copy()

    def has_processed_any_query(self) -> bool:
        """
        Check if we have processed any query yet (for debounce state tracking).

        This is used to determine if we should bypass debounce for the first query.
        It tracks whether we've ever processed a query, not whether we have cached results.

        Returns:
            True if we've processed at least one query (even if it returned empty results).
        """
        with self._lock:
            return self._has_processed_any_query

    def _cleanup_old_queries(self, current_time: float) -> None:
        """
        Remove queries older than CLEANUP_AGE_SECONDS to prevent memory growth.

        Note: This method should only be called from within should_process_query()
        which already holds the lock, so no additional locking is needed here.
        """
        cutoff_time = current_time - self.CLEANUP_AGE_SECONDS
        # Efficient single-pass cleanup
        queries_to_remove = [
            q
            for q, first_seen in self._query_first_seen.items()
            if first_seen < cutoff_time and q != self._last_processed_query
        ]
        for q in queries_to_remove:
            del self._query_first_seen[q]


# Global instance of adaptive debounce manager
_adaptive_debounce_manager = AdaptiveDebounceManager()


def _perform_search(
    search_query: str,
    cached_options: list,
    get_server_options_func,
) -> tuple[list, bool]:
    """
    Perform search across cache and server, combining results.

    This function encapsulates the search strategy:
    - Search client-side cache if available
    - Search server for queries >= 3 chars
    - Combine results, prioritizing cache but adding server matches

    Args:
        search_query: The search query (without prefixes)
        cached_options: Client-side cache options (can be None)
        get_server_options_func: Function to get server options (cached per request)

    Returns:
        Tuple of (matched_options, use_server_fallback) where:
        - matched_options: Combined search results
        - use_server_fallback: True if server results were used/combined
    """
    cache_matches = []
    server_matches = []
    use_server_fallback = False

    # Adjust threshold based on query length - more specific queries can use lower threshold
    search_threshold = 0.15 if len(search_query) >= 4 else 0.2

    # First, the search goes through the client-side cache if available
    if cached_options:
        cache_matches = fuzzy_search(search_query, cached_options, threshold=search_threshold)
        logging.info(f"Cache search found {len(cache_matches)} matches (threshold={search_threshold})")

    # Always also search server for comprehensive results
    # Strategy: Always search server for queries >= 3 chars
    should_search_server = len(search_query) >= 3
    if should_search_server:
        logging.info(
            f"Searching server for query '{search_query}' (length: {len(search_query)}, has_client_cache: {cached_options is not None})"
        )
        try:
            # Use cached server options to avoid redundant fetch
            server_options = get_server_options_func()
            server_matches = fuzzy_search(search_query, server_options, threshold=search_threshold)
            logging.info(f"Server search found {len(server_matches)} matches (threshold={search_threshold})")

        except Exception as e:
            logging.error(f"Server search failed: {str(e)}", exc_info=True)
            server_matches = []
    else:
        logging.debug(
            f"Skipping server search for query '{search_query}' (length: {len(search_query)} < 3, using cache only)"
        )

    # Combine cache and server results (same logic as DEV)
    if not cached_options:
        # No cache available, use server results only
        matched_options = server_matches
        use_server_fallback = True
        logging.info(f"No cache available, using {len(server_matches)} server matches")
    else:
        # Combine cache and server results, prioritizing cache but adding server matches
        matched_options = cache_matches.copy()
        seen_values = set(opt["value"] for opt in cache_matches)
        additional_from_server = []

        for server_match in server_matches:
            if server_match["value"] not in seen_values:
                additional_from_server.append(server_match)
                seen_values.add(server_match["value"])

        matched_options.extend(additional_from_server)
        use_server_fallback = len(additional_from_server) > 0

        logging.info(
            f"Combined results: {len(cache_matches)} from cache + {len(additional_from_server)} from server = {len(matched_options)} total"
        )

        # Explicit verification for debugging
        if should_search_server and len(server_matches) == 0 and len(cache_matches) > 0:
            logging.warning(
                f"WARNING: Server search was requested but returned 0 matches. "
                f"Query: '{search_query}', Cache matches: {len(cache_matches)}, "
                f"Server search executed: {should_search_server}"
            )

    return matched_options, use_server_fallback


def _format_search_results(matched_options: list, prefix_type: Optional[str] = None) -> tuple[list, list]:
    """
    Format search results with prefixes and reorder (orgs first, then repos).

    Args:
        matched_options: Raw search results to format
        prefix_type: Optional prefix filter ("repo" or "org")

    Returns:
        Tuple of (orgs_first, repos_after) - formatted and separated results
    """
    # Filter by prefix type if specified
    if prefix_type == "repo":
        matched_options = [opt for opt in matched_options if SearchItem.from_id(opt["value"]) == SearchItem.REPO]
        logging.info(f"Filtered to {len(matched_options)} repos")
    elif prefix_type == "org":
        matched_options = [opt for opt in matched_options if SearchItem.from_id(opt["value"]) == SearchItem.ORG]
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
        search_item = SearchItem.from_id(opt["value"])

        # Clean repository names by removing URL prefixes
        label = opt["label"]
        if search_item == SearchItem.REPO:
            cleaned_name, platform = clean_repo_name(label)
            # Apply platform-specific prefix
            if platform == "github":
                formatted_opt["label"] = f"GH Repo: {cleaned_name}"
            elif platform == "gitlab":
                formatted_opt["label"] = f"GL Repo: {cleaned_name}"
            else:
                formatted_opt["label"] = f"Repo: {cleaned_name}"
        else:
            formatted_opt["label"] = search_item.prefix(label)
        formatted_opts.append(formatted_opt)

    # Reorder: organizations first, then repositories (single-pass optimization)
    orgs_first = []
    repos_after = []
    for opt in formatted_opts:
        if SearchItem.from_id(opt["value"]) == SearchItem.ORG:
            orgs_first.append(opt)
        else:  # Must be REPO (we filtered earlier)
            repos_after.append(opt)

    logging.info(
        f"Final results breakdown: {len(orgs_first)} orgs, {len(repos_after)} repos, {len(formatted_opts)} total"
    )

    return orgs_first, repos_after


def _handle_selected_options(
    selections: list,
    cached_options: list,
    matched_options: list,
    use_server_fallback: bool,
    get_server_options_func,
) -> list:
    """
    Handle selected options, ensuring they're included in results with proper formatting.

    Args:
        selections: List of selected option values
        cached_options: Client-side cache options
        matched_options: Current matched search results
        use_server_fallback: Whether server results were used
        get_server_options_func: Function to get server options

    Returns:
        List of formatted selected options
    """
    if not selections:
        return []

    selected_options = []

    # First check if selections are in our current options (cache + any server fallback)
    current_selection_values = set(
        opt["value"] for opt in (cached_options or []) + (matched_options if use_server_fallback else [])
    )
    missing_selections = [v for v in selections if v not in current_selection_values]

    # If any selections aren't in our current options, fetch them from the server
    if missing_selections:
        logging.info(f"Fetching {len(missing_selections)} missing selections from server")
        all_options = get_server_options_func()  # Use cached server options
        for v in selections:
            matched_opts = [opt for opt in all_options if opt["value"] == v]
            if matched_opts:
                formatted_v = matched_opts[0].copy()
                if SearchItem.from_id(v) == SearchItem.ORG:
                    formatted_v["label"] = f"org: {formatted_v['label']}"
                elif SearchItem.from_id(v) == SearchItem.REPO:
                    formatted_v["label"] = f"repo: {formatted_v['label']}"
                selected_options.append(formatted_v)
    else:
        # All selections are in our current options
        all_current_options = (cached_options or []) + matched_options
        for v in selections:
            for opt in all_current_options:
                if opt["value"] == v:
                    formatted_v = opt.copy()
                    search_item = SearchItem.from_id(v)
                    formatted_v["label"] = search_item.prefix(opt["label"])
                    selected_options.append(formatted_v)
                    break

    return selected_options


# Note: Login-related callbacks are conditionally registered based on login_enabled
# because when login is disabled, the UI elements (refresh-button, logout-button, etc.)
# don't exist in the layout, which would cause "nonexistent object" callback errors.


def _start_group_collection_login_enabled(url, n_clicks):
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


def _start_group_collection_login_disabled(url):
    """Simplified version when login is disabled - no group collection needed."""
    return dash.no_update


def _login_username_button_enabled(url):
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


def _login_username_button_disabled(url):
    """Simplified version when login is disabled - just shows the login link."""
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
    return [navlink]


@callback(
    [Output("projects", "data")],
    [Input("projects", "searchValue")],
    [State("projects", "value"), State("cached-options", "data")],
)
def dynamic_multiselect_options(user_in: str, selections, cached_options):
    """
    Enhanced search using fuzzy matching and client-side cache with server fallback.
    Implements adaptive debouncing based on query length.

    Args:
        user_in: User's search input
        selections: Currently selected values
        cached_options: All available options from client-side cache
    """
    # Performance monitoring: Track search start time
    search_start_time = time.time()

    if not user_in:
        return dash.no_update

    # Check if we have processed any query yet (for debounce state tracking)
    # This determines if we should bypass debounce for the first query
    has_processed_any_query = _adaptive_debounce_manager.has_processed_any_query()

    # Apply adaptive debouncing (but bypass if no queries processed yet to ensure first query works)
    if has_processed_any_query and not _adaptive_debounce_manager.should_process_query(user_in):
        debounce_ms = get_adaptive_debounce_time(user_in)
        logging.debug(
            f"Query '{user_in[:50]}...' debounced " f"(adaptive debounce: {debounce_ms}ms, length: {len(user_in)})"
        )
        # Return last results instead of no_update to prevent dropdown from showing "no matching"
        # This maintains the dropdown state while debouncing
        # Return cached results even if empty (empty is a valid search result)
        last_results = _adaptive_debounce_manager.get_last_results()
        return [last_results]

    # If no queries processed yet, we bypass debounce and process immediately
    # This ensures the first query always processes and shows results
    if not has_processed_any_query:
        logging.info(
            f"Processing first query '{user_in[:50]}...' immediately (no queries processed yet, bypassing debounce)"
        )
        # Don't mark as processed yet - let the search complete first, then mark it
        # This ensures the search actually happens

    try:
        start_time = time.time()
        debounce_ms = get_adaptive_debounce_time(user_in)
        logging.info(f"Search query: '{user_in}' (adaptive debounce: {debounce_ms}ms)")

        # Cache server options to avoid redundant fetches (used in multiple places)
        _server_options_cache = None

        def _get_server_options():
            """Helper to fetch server options once per request."""
            nonlocal _server_options_cache
            if _server_options_cache is None:
                _server_options_cache = augur.get_multiselect_options().copy()
                logging.info(f"Fetched {len(_server_options_cache)} options from server")
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
                            _server_options_cache = _server_options_cache + user_options
                            logging.info(f"Added {len(user_options)} user options from Redis")
                    except redis.exceptions.ConnectionError as e:
                        logging.error(f"MULTISELECT: Could not connect to users-cache. Error: {str(e)}")
            return _server_options_cache

        # Start with cached options if available
        if cached_options:
            logging.info(f"Using client-side cache with {len(cached_options)} options")
            options = cached_options
        else:
            logging.info("Client-side cache empty, fetching from server")
            options = _get_server_options()

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

        # Perform search across cache and server
        # IMPORTANT: Separation of concerns
        # - Adaptive debounce (has_processed_any_query): Controls WHEN to process (timing concern)
        # - Client-side cache (cached_options): Controls WHAT data source to use (data concern)
        # - Server search condition: Based only on query length
        matched_options, use_server_fallback = _perform_search(
            search_query=search_query,
            cached_options=cached_options,
            get_server_options_func=_get_server_options,
        )

        # Format and reorder search results (orgs first, then repos)
        orgs_first, repos_after = _format_search_results(matched_options, prefix_type=prefix_type)

        # Handle selected options, ensuring they're included with proper formatting
        selected_options = _handle_selected_options(
            selections=selections,
            cached_options=cached_options,
            matched_options=matched_options,
            use_server_fallback=use_server_fallback,
            get_server_options_func=_get_server_options,
        )

        # Combine formatted results: orgs first, then repos
        result = orgs_first + repos_after

        # Add selected options that aren't already in the results
        selected_values = [opt["value"] for opt in result]
        for opt in selected_options:
            if opt["value"] not in selected_values:
                result.append(opt)

        end_time = time.time()
        search_duration = end_time - start_time
        total_duration = end_time - search_start_time

        # Performance monitoring: Log detailed metrics
        logging.info(f"Search completed in {search_duration:.2f} seconds (total: {total_duration:.2f}s)")
        logging.info(f"Returning {len(result)} options to dropdown (fallback used: {use_server_fallback})")

        # Performance monitoring: Log key metrics for analysis
        debounce_ms = get_adaptive_debounce_time(user_in)
        logging.info(
            f"PERF_METRICS: query_len={len(user_in)}, "
            f"search_time_ms={search_duration*1000:.1f}, "
            f"total_time_ms={total_duration*1000:.1f}, "
            f"debounce_ms={debounce_ms}, "
            f"results={len(result)}, "
            f"cache_hit={cached_options is not None}, "
            f"server_fallback={use_server_fallback}"
        )

        # Store results for potential return during debouncing
        _adaptive_debounce_manager.set_last_results(result)

        # Mark query as processed AFTER search completes (for first query that bypassed debounce)
        # This ensures the search actually happened before we mark it as processed
        if not has_processed_any_query:
            _adaptive_debounce_manager.mark_query_processed(user_in)
            logging.debug(
                f"Marked first query '{user_in[:50]}...' as processed after search completed with {len(result)} results"
            )

        return [result]

    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        # Transient network/connection errors - log and return fallback
        logging.error(f"Redis connection error in dynamic_multiselect_options: {str(e)}")
        if selections:
            return _get_fallback_selections(selections)
        return dash.no_update
    except (AttributeError, KeyError, TypeError) as e:
        # Programming errors - should be fixed, but don't crash the app
        logging.error(f"Programming error in dynamic_multiselect_options: {str(e)}", exc_info=True)
        if selections:
            return _get_fallback_selections(selections)
        return dash.no_update
    except Exception as e:
        # Catch-all for unexpected errors
        logging.error(f"Unexpected error in dynamic_multiselect_options: {str(e)}", exc_info=True)
        if selections:
            return _get_fallback_selections(selections)
        return dash.no_update


def _get_fallback_selections(selections: list) -> list:
    """
    Helper function to return fallback options when search fails.

    Args:
        selections: List of selected option values

    Returns:
        List of formatted option dictionaries with basic labels
    """
    default_options = []
    try:
        # Try to get the labels for the current selections
        options = augur.get_multiselect_options()
        for v in selections:
            matched_opts = [opt for opt in options if opt["value"] == v]
            if matched_opts:
                formatted_v = matched_opts[0].copy()
                search_item = SearchItem.from_id(v)
                if search_item == SearchItem.ORG:
                    formatted_v["label"] = f"org: {formatted_v['label']}"
                elif search_item == SearchItem.REPO:
                    formatted_v["label"] = f"repo: {formatted_v['label']}"
                default_options.append(formatted_v)
    except Exception:
        # If that fails, just return the raw selection values
        default_options = [{"value": v, "label": f"ID: {v}"} for v in selections]

    return [default_options]


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
    repos = [int(r) for r in user_vals if SearchItem.from_id(r) == SearchItem.REPO]
    logging.warning(f"REPOS: {repos}")

    # names of augur groups or orgs
    names = [n for n in user_vals if SearchItem.from_id(n) == SearchItem.ORG]

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
    [State("repo-list-alert", "is_open"), State("repo-choices", "data")],
)
def show_repolist_alert(n_clicks, openness, repo_ids):
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

    url_list = [l[8:] if l.startswith("https://") else l for l in url_list]

    element_list = [html.Li(l) for l in url_list]

    elements = [html.Strong("Included Repositories:"), html.Ul(element_list)]

    if n_clicks == 0:
        return dash.no_update, elements
    # switch the openness parameter, allows button to also
    # dismiss the Alert.
    return not openness, elements


@callback(
    [Output("data-badge", "children"), Output("data-badge", "color")],
    [Input("job-ids", "data"), Input("current-page-status", "data"), Input("current-page", "data")],
    background=True,
)
def wait_queries(job_metadata, page_status, current_page):
    """
    Wait for all queries to complete and update the global data badge.

    Shows priority status for current page first, then global status.
    Refactored to use helper utilities following SRP and DRY principles.

    Args:
        job_metadata: Dict mapping {query_name: job_id}
        page_status: Status of current page queries (ready/failed/timeout/idle)
        current_page: Current page path (used for context in logging)

    Returns:
        Tuple of (badge_text, badge_color)
    """
    if not job_metadata:
        return BADGE_TEXT_NO_DATA, BADGE_COLOR_SECONDARY

    # If current page is ready, show page-specific status
    if page_status == PAGE_STATUS_READY:
        # Check if ALL queries are done for global status
        if check_all_jobs_complete(job_metadata):
            return BADGE_TEXT_ALL_READY, BADGE_COLOR_READY
        else:
            return BADGE_TEXT_PAGE_READY, BADGE_COLOR_LOADING
    elif page_status == PAGE_STATUS_FAILED:
        return BADGE_TEXT_PAGE_FAILED, BADGE_COLOR_ERROR
    elif page_status == PAGE_STATUS_TIMEOUT:
        return BADGE_TEXT_PAGE_TIMEOUT, BADGE_COLOR_WARNING

    # Create AsyncResult objects for non-cached jobs
    jobs, query_names = create_async_results_from_metadata(job_metadata)

    # If all queries were cached, we're done
    if not jobs:
        return BADGE_TEXT_DATA_READY, BADGE_COLOR_READY

    # Wait for all jobs to complete
    status, message = wait_for_job_completion(jobs, query_names, context="wait_queries")

    # Clean up job results
    forget_jobs(jobs)

    # Map status to badge text and color
    if status == PAGE_STATUS_READY:
        return BADGE_TEXT_DATA_READY, BADGE_COLOR_READY
    elif status == PAGE_STATUS_FAILED:
        return BADGE_TEXT_DATA_INCOMPLETE, BADGE_COLOR_ERROR
    elif status == PAGE_STATUS_TIMEOUT:
        return BADGE_TEXT_TIMEOUT_RETRY, BADGE_COLOR_WARNING
    else:
        return BADGE_TEXT_NO_DATA, BADGE_COLOR_SECONDARY


@callback(
    Output("current-page", "data"),
    Input("url", "pathname"),
)
def track_current_page(pathname):
    """Track which page the user is currently on for priority loading."""
    return pathname


@callback(
    Output("current-page-status", "data"),
    [Input("current-page", "data"), Input("job-ids", "data"), Input("repo-choices", "data")],
    background=True,
)
def wait_current_page_queries(current_page, job_metadata, repos):
    """
    Wait for the current page's queries to complete with high priority.

    This runs in the background and aggressively polls only the queries needed
    for the current page, enabling faster page load times.
    Refactored to use helper utilities following SRP and DRY principles.

    Args:
        current_page: URL path of current page (e.g., "/contributions")
        job_metadata: Dict mapping {query_name: job_id}
        repos: List of repo IDs being queried

    Returns:
        Status string: "idle", "ready", "failed", or "timeout"
    """
    if not current_page or not job_metadata or not repos:
        return PAGE_STATUS_IDLE

    # Get the queries needed for the current page
    page_query_names = get_page_query_names(current_page)

    if not page_query_names:
        logging.info(f"No queries mapped for page: {current_page}")
        return PAGE_STATUS_IDLE

    # Create AsyncResult objects for current page queries only
    jobs, query_names = create_async_results_from_metadata(job_metadata, page_query_names)

    # If all current page queries are cached
    if not jobs:
        logging.info(f"All queries for {current_page} are cached")
        return PAGE_STATUS_READY

    logging.info(f"Waiting for {len(jobs)} queries for page: {current_page}")

    # Wait with aggressive polling for current page (faster than background queries)
    status, message = wait_for_job_completion(
        jobs,
        query_names,
        poll_interval=CURRENT_PAGE_POLL_INTERVAL,  # 0.5s - faster polling
        max_wait_time=MAX_QUERY_WAIT_TIME,
        context=current_page,
    )

    # Note: We don't forget jobs here as they may still be needed by wait_queries()
    # Celery will clean them up automatically based on result_expires config

    return status


@callback(
    Output("job-ids", "data"),
    Input("repo-choices", "data"),
)
def run_queries(repos):
    """
    Executes queries defined in /queries against Augur
    instance for input Repos; caches results in Postgres.

    Returns a dict mapping query names to job IDs for tracking.

    Args:
        repos ([int]): repositories we collect data for.
    """

    # cache manager object
    cache = cm()

    # list of queries to process
    funcs = QUERIES

    # dict to store job metadata: {query_name: job_id}
    job_metadata = {}

    for f in funcs:
        # only download repos that aren't currently in cache
        not_ready = cf.get_uncached(f.__name__, repos)
        if len(not_ready) == 0:
            logging.warning(f"{f.__name__} - NO DISPATCH - ALL REPOS IN CACHE")
            # Mark as cached/complete
            job_metadata[f.__name__] = QUERY_STATUS_CACHED
            continue

        # add job to queue
        j = f.apply_async(args=[not_ready], queue="data")

        # store job ID with query name
        job_metadata[f.__name__] = j.id
        logging.info(f"{f.__name__} - DISPATCHED - Job ID: {j.id}")

    return job_metadata


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
        repos = [opt for opt in options if SearchItem.from_id(opt.get("value")) == SearchItem.REPO][:max_repos]

        # For orgs, keep all (there are usually only a few hundred)
        orgs = [opt for opt in options if SearchItem.from_id(opt.get("value")) == SearchItem.ORG]

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


# Enhanced search progress indicator with adaptive debounce feedback
@callback(
    [Output("search-progress-indicator", "children"), Output("search-progress-indicator", "style")],
    [Input("projects", "searchValue")],
    prevent_initial_call=True,
)
def update_search_progress_indicator(search_value):
    """
    Update the search progress indicator with adaptive debounce information.
    This provides visual feedback to users about search state and expected wait time.
    """
    if not search_value:
        return ["", {"display": "none"}]

    # Get adaptive debounce time for this query
    debounce_ms = get_adaptive_debounce_time(search_value)

    # Determine message based on query characteristics
    query_length = len(search_value)

    if query_length <= 2:
        # Very short queries - user still typing
        message = "Refining..."
        color = "#888"
    elif query_length <= 5:
        # Medium queries - user may be finishing
        message = "Searching..."
        color = "#0F5880"  # Brand blue
    else:
        # Long queries - likely complete, searching fast
        message = "Searching..."
        color = "#0F5880"

    # Show indicator with appropriate styling
    style = {
        "position": "absolute",
        "right": "16px",
        "top": "50%",
        "transform": "translateY(-50%)",
        "fontSize": "11px",
        "color": color,
        "fontWeight": "500",
        "display": "flex",
        "alignItems": "center",
        "gap": "6px",
        "zIndex": 2,
        "whiteSpace": "nowrap",
        "animation": "pulse 1.5s ease-in-out infinite",
    }

    return [message, style]


# Hide progress indicator when results are loaded
@callback(
    [Output("search-progress-indicator", "style", allow_duplicate=True)],
    [Input("projects", "data")],
    prevent_initial_call=True,
)
def hide_search_progress_when_loaded(_):
    """Hide the search progress indicator when results are loaded."""
    return [{"display": "none"}]


# =============================================================================
# CONDITIONAL CALLBACK REGISTRATION
# =============================================================================
# When login is disabled, the UI elements referenced by these callbacks
# (refresh-button, logout-button, # manage-group-button, login-popover)
# do not exist in the layout, which would
# cause "nonexistent object was used in an Input" callback errors.
#
# This conditional registration prevents those errors by only registering
# callbacks for UI elements that actually exist in the current configuration.
# =============================================================================

if login_enabled:
    # Register callbacks with full login functionality
    callback(
        [Output("user-group-loading-signal", "data")],
        [Input("url", "href"), Input("refresh-button", "n_clicks")],
    )(_start_group_collection_login_enabled)

    callback(
        [
            Output("nav-login-container", "children"),
            Output("login-popover", "is_open"),
            Output("refresh-button", "disabled"),
            Output("logout-button", "disabled"),
            Output("manage-group-button", "disabled"),
        ],
        Input("url", "href"),
    )(_login_username_button_enabled)
else:
    # Register simplified callbacks when login is disabled
    callback(
        [Output("user-group-loading-signal", "data")],
        [Input("url", "href")],
    )(_start_group_collection_login_disabled)

    callback(
        [Output("nav-login-container", "children")],
        Input("url", "href"),
    )(_login_username_button_disabled)


# Callback to handle sidebar collapse/expand functionality using dbc.Collapse
@callback(
    Output("sidebar-collapse", "is_open"),
    [Input("sidebar-toggle", "n_clicks"), Input("url", "pathname")],
    State("sidebar-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_sidebar_collapse(n_clicks, pathname, is_open):
    """Toggle the sidebar using dbc.Collapse component and auto-open for visualization pages."""
    ctx = dash.callback_context

    # Check which input triggered the callback
    if ctx.triggered_id == "sidebar-toggle" and n_clicks:
        # Manual toggle - simply toggle the collapse state
        return not is_open
    elif ctx.triggered_id == "url":
        # URL change - check if we should auto-open for visualization pages
        visualization_paths = [
            "/repo_overview",
            "/contributions",
            "/contributors/behavior",
            "/contributors/contribution_types",
            "/affiliation",
            "/chaoss",
        ]

        # Check if current path starts with any visualization path
        should_open = any(pathname.startswith(path) for path in visualization_paths if pathname)

        if should_open and not is_open:
            return True

    return dash.no_update


# Callback to adjust main content area when sidebar state changes
@callback(
    Output("page-container", "style"),
    Input("sidebar-collapse", "is_open"),
    prevent_initial_call=True,
)
def adjust_content_area_collapse(is_open):
    """Adjust the main content area styling based on sidebar collapse state."""
    # Base styling that doesn't change
    base_style = {
        "background-color": "#1D1D1D",
        "padding": "1rem",  # Restore normal padding
        "overflow-y": "auto",
        "height": "100%",
        "flex": "1",
        "transition": "border-radius 0.3s ease",
    }

    # Only modify the border-radius based on sidebar state
    if not is_open:
        # When sidebar is collapsed, content area takes full width with rounded corners
        base_style["border-radius"] = "12px"
    else:
        # When sidebar is expanded, content area has right-side border radius only
        base_style["border-radius"] = "0 12px 12px 0"

    return base_style


# Callback to hide loading components on landing page
@callback(
    [
        Output("results-output-container", "style"),
        Output("data-badge", "style"),
    ],
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def hide_loading_on_landing(pathname):
    """Hide loading components when on landing page."""
    if pathname == "/" or pathname is None:
        # Hide loading components on landing page
        return {"display": "none"}, {"display": "none"}
    else:
        # Show loading components on other pages
        return {"display": "block"}, {"marginBottom": ".5%", "display": "inline-block"}


# Note: Landing page callbacks moved to pages/landing/landing_callbacks.py


# ============================================================================
# Callback to change pill color when search is clicked
#
# This callback implements dynamic pill coloring:
# - When user selects repos/orgs: pills are grey (pending)
# - When user clicks search icon: pills turn blue (active search)
# - Default selection (chaoss) starts blue since search is auto-triggered
#
# Works in conjunction with CSS in main_layout.css
# ============================================================================
@callback(
    Output("projects", "className"),
    [Input("search", "n_clicks"), Input("projects", "value")],
    prevent_initial_call=True,
)
def update_pill_color_on_search(_, selected_repos_orgs):
    """Update pill color based on search action.

    When search icon is clicked, add 'searching' class to turn pills blue.
    When values change (user is selecting), remove 'searching' class to keep pills grey.
    """
    if not dash.ctx.triggered:
        return dash.no_update

    triggered_id = dash.ctx.triggered_id

    if triggered_id == "search":
        # Search button clicked - add 'searching' class to turn pills blue
        logging.info(f"PILL COLOR: Search clicked - turning pills BLUE")
        return "searchbar-dropdown searching"
    if triggered_id == "projects":
        # Values changed (user selecting) - remove 'searching' class to keep pills grey
        logging.info(f"PILL COLOR: Values changed - turning pills GREY. Selected: {selected_repos_orgs}")
        return "searchbar-dropdown"

    return dash.no_update
