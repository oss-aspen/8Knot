from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

# Maps each visualization page (its URL pathname) to the graph IDs that page
# actually renders. The graph IDs here are the real VIZ_ID values emitted by
# the share buttons (id={"type": "share-btn", "graph": viz_id, ...}) — NOT the
# sidebar anchor fragments, which live in a different identifier space.
#
# This is the single source of truth for share-link target validation. It is
# kept in sync with the live viz pages by ``tests/url_registry_test.py``, which
# re-derives this mapping from the page layouts and fails on any drift.
VALID_GRAPH_REGISTRY: dict[str, list[str]] = {
    "/repo_overview": [
        "code-languages",
        "ossf-scorecard",
        "package-version",
        "repo-general-info",
    ],
    "/contributions": [
        "cntrib-pr-assignment",
        "cntrib_issue-assignment",
        "commits-over-time",
        "issue-staleness",
        "issue_assignment",
        "issues-over-time",
        "pr-first-response",
        "pr-review-response",
        "pr-staleness",
        "pr_assignment",
        "prs-over-time",
        "self-merge",
    ],
    "/contributors/behavior": [
        "active-drifting-contributors",
        "contrib-drive-repeat",
        "contrib-types-over-time",
        "first-time-contribution",
        "new-contributor",
    ],
    "/contributors/contribution_types": [
        "contrib-activity-cycle",
        "contrib-importance-pie",
        "contribs-by-action",
        "lottery-factor-over-time",
    ],
    "/chaoss": [
        "contrib-importance-pie",
        "project-velocity",
    ],
    "/affiliation": [
        "commit-domains",
        "gh-org-affiliation",
        "org-core-contributors",
        "organization-associated-activity",
        "unique-domains",
    ],
    "/codebase": [
        "cntrb-file-heatmap",
        "contribution-file-heatmap",
        "reviewer-file-heatmap",
    ],
}

# Maps a removed/renamed (pathname, graph_id) to its replacement (or None when
# dropped with no successor). This is the migration seam: when a graph moves or
# is retired, add an entry here so old shared links resolve gracefully instead
# of dead-ending.
DEPRECATED_GRAPH_REGISTRY: dict[tuple, tuple | None] = {}


def validate_target(pathname: str, graph_id: str | None) -> tuple[bool, tuple | None]:
    """Return ``(is_valid, redirect)`` for a shared link target.

    A target is valid when its pathname is a known viz page AND its graph_id is
    either absent (no specific graph) or one this page actually renders. An
    unknown graph on a known page is treated as removed, so it can fall through
    to the deprecation registry (and otherwise reads as "no longer exists").
    """
    graphs = VALID_GRAPH_REGISTRY.get(pathname)
    if graphs is not None and (graph_id is None or graph_id in graphs):
        return True, None
    deprecated = DEPRECATED_GRAPH_REGISTRY.get((pathname, graph_id))
    if deprecated is not None:
        return False, deprecated
    return False, None


def _compose_url(base: str, pathname: str, query: str, graph_id: str | None) -> str:
    """Assemble ``<base><pathname>?<query>[#graph_id]``.

    Single source of truth for share-URL formatting so the short/long
    variants can never drift apart.
    """
    frag = f"#{graph_id}" if graph_id else ""
    return f"{base.rstrip('/')}{pathname}?{query}{frag}"


def compose_short_url(base: str, short_id: str, pathname: str, graph_id: str | None) -> str:
    return _compose_url(base, pathname, f"s={short_id}", graph_id)


def compose_long_url(base: str, encoded_state: str, pathname: str, graph_id: str | None) -> str:
    return _compose_url(base, pathname, f"state={encoded_state}", graph_id)


def extract_base_url(href: str) -> str:
    """Return ``scheme://netloc`` from a full href, robust to path collisions.

    Using urlsplit (rather than string slicing on the pathname) means a
    hostname that happens to contain the pathname can't corrupt the result.
    """
    parts = urlsplit(href or "")
    return f"{parts.scheme}://{parts.netloc}"


def extract_url_params(search: str) -> dict:
    if not search:
        return {}
    params = parse_qs(search.lstrip("?"))
    return {
        "short_id": (params.get("s") or [None])[0],
        "state": (params.get("state") or [None])[0],
    }
