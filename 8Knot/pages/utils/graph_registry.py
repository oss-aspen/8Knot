"""
Registry of valid (pathname, graph_id) share targets, plus validation.

This is domain knowledge — *which* visualizations exist on *which* pages — so
it lives apart from the pure string helpers in ``url_utils.py``. A utility
module should not need editing every time a visualization page changes; this
one does.

The graph IDs here are the real ``VIZ_ID`` values emitted by the share buttons
(``id={"type": "share-btn", "graph": viz_id, ...}``) — NOT the sidebar anchor
fragments, which live in a different identifier space.

This is the single source of truth for share-link target validation. It is
meant to be kept in sync with the live viz pages by a drift test that
re-derives the mapping from the page layouts (see the follow-up test PR).
"""

from __future__ import annotations

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
