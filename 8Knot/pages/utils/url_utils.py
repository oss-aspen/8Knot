"""
Pure URL helpers for the shareable-link system.

String composition and parsing only — no Dash coupling and no knowledge of
which graphs exist (that domain logic lives in ``graph_registry.py``).
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit


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
