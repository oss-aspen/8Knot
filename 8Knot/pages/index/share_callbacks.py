"""
Callbacks for the shareable URL system.

Kept in its own module (rather than in the already-large
`index_callbacks.py`) so the share feature is self-contained: layout lives
in `share_components.py`, pure encode/decode + shortener logic live in
`cache_manager/`, and this file is only the Dash wiring plus a couple of
thin orchestration helpers.

Two-layer design
----------------
  Layer 1 (state): ?state=<gzip+base64url payload>  — self-contained, no DB.
  Layer 2 (short): ?s=<short_id>                     — DB lookup -> payload.

Integration rules (learned the hard way — see share_components.py)
------------------------------------------------------------------
  * Share UI lives in `share_components.create_share_modal()`, NOT in the
    app stores list.
  * The load path NEVER writes `repo-choices` directly. It populates
    `projects` and bumps `search-button.n_clicks`, reusing the existing
    `multiselect_values_to_repo_ids` pipeline. This avoids `allow_duplicate`
    races on `repo-choices`.
  * Only ONE callback reads `url.search`.
  * Share-button pattern-matching IDs are used as callback INPUTS only;
    every OUTPUT targets a simple string-id modal component.
"""

import logging

import dash
from dash import callback, ctx, clientside_callback
from dash.dependencies import Input, Output, State, ALL

from app import augur
import cache_manager.url_state as url_state
import cache_manager.share_manager as share_manager
from cache_manager.cx_common import cache_connection
from pages.utils import url_utils
from models import SearchItem


# -----------------------------------------------------------------------------
# Helpers (pure orchestration — no Dash coupling, easy to read and test)
# -----------------------------------------------------------------------------


def _split_selection(selection):
    """Split a raw searchbar selection into ``(repo_ids, org_names)``.

    The searchbar stores orgs/groups as non-numeric values and repos as
    numeric values (see ``SearchItem.from_id``). We persist them separately so
    a shared link keeps an org *as an org* — restoring the single org pill
    instead of its dozens of expanded repos, and re-resolving the org on load
    (which also picks up repos added to it since the link was made).
    """
    repo_ids, org_names = [], []
    for v in selection or []:
        if SearchItem.from_id(v) == SearchItem.REPO:
            repo_ids.append(int(v))
        else:
            org_names.append(v)
    return repo_ids, org_names


def _build_share_url(selection, pathname, href, page, graph_id):
    """Encode the searchbar selection and return ``(url, warning_message)``.

    Prefers a short ``?s=`` link; on any DB failure falls back to a
    self-contained ``?state=`` long link (Layer 1) so sharing still works
    even when the shortener is unavailable.

    The payload stores ``graph_id`` as the bare VIZ_ID (what the registry
    validates against), but the URL *fragment* must be the card's real DOM id
    — ``f"{page}-{viz_id}"`` (see ``VisualizationAIO``) — or the browser has
    nothing to scroll to.
    """
    repo_ids, org_names = _split_selection(selection)
    base_url = url_utils.extract_base_url(href)
    encoded = url_state.encode_state(
        repo_ids=repo_ids,
        org_names=org_names,
        pathname=pathname,
        graph_id=graph_id,
    )
    anchor = f"{page}-{graph_id}" if (page and graph_id) else None
    try:
        with cache_connection() as conn:
            short_id = share_manager.shorten(conn, encoded)
        return url_utils.compose_short_url(base_url, short_id, pathname, anchor), ""
    except Exception as e:
        logging.error(f"SHARE: shorten failed, falling back to long URL: {e}")
        long_url = url_utils.compose_long_url(base_url, encoded, pathname, anchor)
        return long_url, "Short-link service unavailable — using a full link."


def _resolve_selection(repo_ids, org_names):
    """Rebuild searchbar options/values from a decoded payload.

    Returns ``(options, values, missing)``. Each present repo/org must yield a
    matching ``{value, label}`` option because dmc.MultiSelect only keeps
    values that also appear in its ``data``. ``repo_id_to_git`` / ``is_org``
    are in-memory lookups that report whether the item still exists on THIS
    instance — which is how we honor the "load remaining + warn" behavior.
    """
    options, values, missing = [], [], []

    for rid in repo_ids:
        git_url = augur.repo_id_to_git(rid)
        if git_url:
            label = git_url[8:] if git_url.startswith("https://") else git_url
            options.append({"value": str(rid), "label": label})
            values.append(str(rid))
        else:
            missing.append(rid)

    for org in org_names:
        if augur.is_org(org):
            options.append({"value": org, "label": org})
            values.append(org)
        else:
            missing.append(org)

    return options, values, missing


# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


@callback(
    Output("share-modal", "is_open"),
    Output("share-url-display", "value"),
    Output("share-warning-text", "children"),
    Output("share-status-message", "children"),
    Input({"type": "share-btn", "graph": ALL, "page": ALL}, "n_clicks"),
    Input("share-modal-close", "n_clicks"),
    State("projects", "value"),
    State("url", "pathname"),
    State("url", "href"),
    prevent_initial_call=True,
)
def manage_share_modal(share_clicks, close_clicks, selection, pathname, href):
    """Open the share modal with a generated link, or close it.

    One callback owns ``share-modal.is_open``, so no ``allow_duplicate`` is
    needed. The share buttons are pattern-matched inputs; the triggering
    graph is recovered from ``ctx.triggered_id``.

    We share the searchbar *selection* (``projects.value``) rather than the
    resolved ``repo-choices`` so an org is preserved as an org (not exploded
    into its member repos).
    """
    triggered = ctx.triggered_id

    # Close button.
    if triggered == "share-modal-close":
        return False, "", "", ""

    # Pattern inputs can fire with all-None on layout changes; ignore those.
    if not isinstance(triggered, dict) or not any(c for c in (share_clicks or []) if c):
        raise dash.exceptions.PreventUpdate

    if not selection:
        return True, "", "Run a search (select repositories) before sharing.", ""

    url, warning = _build_share_url(selection, pathname, href, triggered.get("page"), triggered.get("graph"))
    return True, url, warning, ""


# Clipboard copy is done client-side to avoid the `dcc.Clipboard` render
# quirks that contributed to earlier breakage. `clientside_callback` is
# imported from dash so it registers on the global app without needing the
# app object (which isn't defined yet when this module is imported).
clientside_callback(
    """
    function(n_clicks, url) {
        if (!n_clicks || !url) { return window.dash_clientside.no_update; }
        var fallback = "Copy failed — press Ctrl/Cmd+C to copy the selected link.";
        // navigator.clipboard is undefined on insecure (HTTP) contexts, and
        // writeText returns a promise that can reject (permission denied).
        // Returning the promise lets Dash report the TRUE outcome rather than
        // optimistically claiming success.
        if (!navigator.clipboard) { return fallback; }
        return navigator.clipboard.writeText(url)
            .then(function () { return "Link copied to clipboard!"; })
            .catch(function () { return fallback; });
    }
    """,
    Output("share-status-message", "children", allow_duplicate=True),
    Input("share-copy-button", "n_clicks"),
    State("share-url-display", "value"),
    prevent_initial_call=True,
)


@callback(
    Output("share-loaded-state", "data"),
    Output("share-load-alert", "is_open"),
    Output("share-load-alert", "children"),
    Input("url", "search"),
    prevent_initial_call=False,
)
def handle_share_url(search):
    """Resolve a ``?s=`` or ``?state=`` URL into a payload for the load pipeline.

    This is the ONLY callback that reads ``url.search``. It writes to a
    dedicated store (``share-loaded-state``) and an isolated alert — never to
    components owned by other callbacks — so it is safe to run on initial
    page load alongside Dash's built-in page routing.
    """
    params = url_utils.extract_url_params(search)
    short_id = params.get("short_id")
    raw_state = params.get("state")

    if short_id:
        try:
            with cache_connection() as conn:
                raw_state = share_manager.expand(conn, short_id)
        except Exception as e:
            logging.error(f"SHARE: expand failed: {e}")
            return None, True, "Could not load shared link (lookup failed)."
        if raw_state is None:
            return None, True, "This shared link has expired or was not found."

    if not raw_state:
        # Normal navigation with no share params — do nothing.
        raise dash.exceptions.PreventUpdate

    state = url_state.decode_state(raw_state)
    if state is None:
        return None, True, "This shared link is in an outdated or invalid format."

    is_valid, _ = url_utils.validate_target(state.get("pathname"), state.get("graph_id"))
    if not is_valid:
        return None, True, "The graph referenced by this link no longer exists."

    repo_ids = state.get("repo_ids", [])
    org_names = state.get("org_names", [])
    options, values, missing = _resolve_selection(repo_ids, org_names)

    if not values:
        return None, True, "None of the repositories/organizations in this link are available on this instance."

    payload = {"options": options, "values": values}

    if missing:
        total = len(repo_ids) + len(org_names)
        msg = (
            f"Loaded {len(values)} of {total} selections. " f"{len(missing)} are no longer available on this instance."
        )
        return payload, True, msg

    return payload, False, ""


@callback(
    Output("projects", "data", allow_duplicate=True),
    Output("projects", "value"),
    Output("search-button", "n_clicks"),
    Input("share-loaded-state", "data"),
    State("search-button", "n_clicks"),
    prevent_initial_call=True,
)
def apply_share_state(loaded, current_clicks):
    """Drive the existing search pipeline from a loaded share payload.

    Populates the searchbar's ``data`` (so dmc.MultiSelect keeps the values),
    sets the selection, and programmatically bumps ``search-button.n_clicks``.
    The existing ``multiselect_values_to_repo_ids`` callback then populates
    ``repo-choices`` exactly as a manual search would — so graphs render
    through the normal path with no duplicated ``repo-choices`` writes.

    ``projects.data`` uses ``allow_duplicate=True``: its base writer
    (``dynamic_multiselect_options``) fires on ``projects.searchValue``, a
    completely separate trigger, so the two never race.
    """
    if not loaded or not loaded.get("values"):
        raise dash.exceptions.PreventUpdate

    return loaded["options"], loaded["values"], (current_clicks or 0) + 1


# Scroll the shared graph into view. A Dash multi-page app renders page content
# client-side, so the browser's native hash scroll fires before the target card
# exists; worse, graphs ABOVE the target finish loading their data afterwards
# and reflow the page, pushing the target out of view. So we:
#   1. retry until the target card exists (it appears before its graph data),
#   2. re-scroll at a few growing delays to correct for that async reflow,
#   3. stop the moment the user scrolls themselves, so we never fight them.
# block:'center' keeps the graph visible despite the fixed topbar and minor
# reflow. Keyed on url.hash, so the sidebar "#graph" anchors benefit too.
clientside_callback(
    """
    function(hash_, _loaded) {
        if (!hash_) { return window.dash_clientside.no_update; }
        var id = decodeURIComponent(hash_.replace(/^#/, ''));
        var cancelled = false;
        function onUserScroll() { cancelled = true; }
        function scrollToTarget() {
            if (cancelled) { return true; }
            var el = document.getElementById(id);
            if (!el) { return false; }
            el.scrollIntoView({behavior: 'smooth', block: 'center'});
            return true;
        }
        var tries = 0;
        (function findThenScroll() {
            if (cancelled) { return; }
            if (scrollToTarget()) {
                window.addEventListener('wheel', onUserScroll, {passive: true, once: true});
                window.addEventListener('touchmove', onUserScroll, {passive: true, once: true});
                [400, 1000, 2000, 3500, 5500].forEach(function(d) { setTimeout(scrollToTarget, d); });
                return;
            }
            if (tries++ < 20) { setTimeout(findThenScroll, 250); }
        })();
        return window.dash_clientside.no_update;
    }
    """,
    Output("share-scroll-dummy", "data"),
    Input("url", "hash"),
    Input("share-loaded-state", "data"),
    prevent_initial_call=False,
)
