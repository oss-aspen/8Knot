from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

VALID_GRAPH_REGISTRY: dict[str, list[str]] = {
    "/repo_overview": [
        "code-languages",
        "package-version",
        "per-repo-analysis",
    ],
    "/contributions": [
        "commits-over-time",
        "prs-over-time",
        "pr-staleness",
        "self-merge-rate",
        "pr-first-response",
        "pr-review-response",
        "pr_assignment",
        "cntrib-pr-assignment",
        "issues-over-time",
        "issue-staleness",
        "issue_assignment",
        "cntrib-issue-assignment",
    ],
    "/contributors/behavior": [
        "drive-throughs",
        "first-time-contributors",
        "engagement-growth",
        "new-contributors",
        "contributor-types",
    ],
    "/contributors/contribution_types": [
        "contributor-actions",
        "contributor-activity-cycle",
        "lottery-factor-snapshot",
        "lottery-factor-time",
    ],
    "/chaoss": [
        "lottery-factor",
        "project-velocity",
    ],
    "/affiliation": [
        "commits-by-domain",
        "unique-domains",
        "org-activity",
        "org-core-contributors",
        "gh-org-affiliation",
    ],
    "/codebase": [
        "contribution-file-heatmap",
        "cntrb-file-heatmap",
        "reviewer-file-heatmap",
    ],
}

DEPRECATED_GRAPH_REGISTRY: dict[tuple, tuple | None] = {}


def validate_target(pathname: str, graph_id: str | None) -> tuple[bool, tuple | None]:
    if pathname in VALID_GRAPH_REGISTRY:
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
