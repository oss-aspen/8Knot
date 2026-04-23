"""
URL state serialization and deserialization for shareable links.

This module is the single source of truth for how application state
maps to and from the URL query string.

State covered (Step 1 — global selection):
    repos   - comma-separated owner/repo slugs
    orgs    - comma-separated org names
    bots    - "on" | "off"  (bot-filter switch)

Usage:
    from pages.utils.url_state import parse_url_params, build_url_params

    # On page load — turn ?repos=...&orgs=...&bots=off into a dict
    state = parse_url_params(url_search_string)

    # On Search click — turn current selections into a query string
    search = build_url_params(repo_ids, org_names, bots_on, augur)
"""

import logging
import os
from typing import Optional
from urllib.parse import urlencode, parse_qs

# =============================================================================
# Constants
# =============================================================================

# Bot filter URL parameter values
BOTS_FILTER_OFF = "off"
BOTS_FILTER_ON = "on"

# URL parameter names
PARAM_REPOS = "repos"
PARAM_ORGS = "orgs"
PARAM_BOTS = "bots"

# ---------------------------------------------------------------------------
# Slug ↔ repo_id helpers
# ---------------------------------------------------------------------------

# Default platform URL prefixes for slug conversion
# To add support for additional platforms (e.g., Bitbucket, Gitea):
# 1. Add the platform prefix to this list, OR
# 2. Set GIT_PLATFORM_PREFIXES environment variable with comma-separated prefixes:
#    export GIT_PLATFORM_PREFIXES="https://github.com/,https://gitlab.com/,https://bitbucket.org/"
_DEFAULT_PREFIXES = [
    "https://github.com/",
    "https://gitlab.com/",
    "http://github.com/",
    "http://gitlab.com/",
]


def _get_known_prefixes() -> list[str]:
    """Get the list of known git platform prefixes.

    Checks for GIT_PLATFORM_PREFIXES environment variable first,
    falls back to default prefixes if not set.

    Returns:
        List of URL prefixes (e.g., ["https://github.com/", ...])
    """
    env_prefixes = os.getenv("GIT_PLATFORM_PREFIXES")
    if env_prefixes:
        # Parse comma-separated list, strip whitespace, ensure trailing slash
        prefixes = [p.strip() for p in env_prefixes.split(",") if p.strip()]
        # Normalize: ensure each prefix ends with /
        return [p if p.endswith("/") else p + "/" for p in prefixes]
    return _DEFAULT_PREFIXES


# Cache the prefix list (computed once at module load)
_KNOWN_PREFIXES = _get_known_prefixes()


def git_url_to_slug(git_url: str) -> Optional[str]:
    """Convert a full git URL to an owner/repo slug.

    Examples:
        "https://github.com/oss-aspen/8Knot" -> "oss-aspen/8Knot"
        "https://gitlab.com/inkscape/inkscape" -> "inkscape/inkscape"
        Unrecognised format -> None (skip silently)
    """
    if not git_url:
        return None
    for prefix in _KNOWN_PREFIXES:
        if git_url.lower().startswith(prefix):
            slug = git_url[len(prefix) :].rstrip("/")
            return slug if slug else None
    return None


def slug_to_repo_id(slug: str, augur) -> Optional[int]:
    """Resolve an owner/repo slug back to an augur repo_id.

    Tries common platform prefixes until a match is found.
    Returns None when the slug is not in this Augur instance.
    """
    for prefix in _KNOWN_PREFIXES:
        full_url = prefix + slug
        repo_id = augur.repo_git_to_id(full_url)
        if repo_id is not None:
            return repo_id
    # Also try without any prefix (some instances store bare slugs)
    repo_id = augur.repo_git_to_id(slug)
    return repo_id  # may be None


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------


def parse_url_params(search: str) -> dict:
    """Parse the URL query string into a state dict.

    Args:
        search: The raw query string, e.g. "?repos=oss-aspen/8Knot&bots=off"
                May or may not include the leading "?".

    Returns:
        dict with keys: "repos", "orgs", "bots"
        All keys are always present; missing params get None / default values.

        {
            "repos": ["oss-aspen/8Knot", "chaoss/augur"],  # list of slugs
            "orgs":  ["chaoss"],                            # list of org names
            "bots":  True,                                  # bool
        }
    """
    if not search:
        return {}

    # parse_qs needs the leading "?" stripped
    clean = search.lstrip("?")
    params = parse_qs(clean, keep_blank_values=False)

    result = {}

    # repos — csv split, strip whitespace, drop empties
    raw_repos = params.get(PARAM_REPOS, [None])[0]
    if raw_repos:
        result[PARAM_REPOS] = [s.strip() for s in raw_repos.split(",") if s.strip()]

    # orgs — csv split
    raw_orgs = params.get(PARAM_ORGS, [None])[0]
    if raw_orgs:
        result[PARAM_ORGS] = [s.strip() for s in raw_orgs.split(",") if s.strip()]

    # bots — BOTS_FILTER_OFF is the only falsy value; everything else (incl. missing) = True
    raw_bots = params.get(PARAM_BOTS, [None])[0]
    if raw_bots is not None:
        result[PARAM_BOTS] = raw_bots.lower() != BOTS_FILTER_OFF

    return result


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build_url_params(repo_ids: list, org_names: list, bots_on: bool, augur) -> str:
    """Serialize the current selection state into a URL query string.

    Args:
        repo_ids:  List of integer repo IDs from repo-choices store.
        org_names: List of org name strings from projects.value.
        bots_on:   Current value of the bot-switch (True = filter bots).
        augur:     AugurManager instance (for repo_id → git URL lookup).

    Returns:
        A URL query string starting with "?", e.g.
        "?repos=oss-aspen/8Knot,chaoss/augur&orgs=chaoss&bots=off"
        Returns "" when there is nothing to encode.
    """
    params = {}

    # repos: convert IDs → git URLs → slugs
    slugs = []
    for rid in repo_ids:
        git_url = augur.repo_id_to_git(int(rid))
        if git_url:
            slug = git_url_to_slug(git_url)
            if slug:
                slugs.append(slug)
            else:
                logging.warning(f"URL_STATE: unrecognised git URL format: {git_url!r}")
    if slugs:
        params[PARAM_REPOS] = ",".join(slugs)

    # orgs: already human-readable strings
    if org_names:
        params[PARAM_ORGS] = ",".join(org_names)

    # bots: only encode when the filter is OFF (on is the default — skip it)
    if not bots_on:
        params[PARAM_BOTS] = BOTS_FILTER_OFF

    if not params:
        return ""

    return "?" + urlencode(params)


# ---------------------------------------------------------------------------
# Resolve URL state → multiselect value list + unknown slugs report
# ---------------------------------------------------------------------------


def resolve_url_state(parsed: dict, augur) -> tuple[list, list]:
    """Convert a parsed URL state dict into a projects.value list.

    Args:
        parsed: Output of parse_url_params().
        augur:  AugurManager instance.

    Returns:
        (values, unknown_slugs)
        values        — list ready to set as projects.value
                        (numeric-string repo IDs + org name strings)
        unknown_slugs — slugs that could not be resolved in this Augur instance

    Return type: tuple[list, list]
    """
    if not parsed:
        return [], []

    values = []
    unknown_slugs = []

    for slug in parsed.get(PARAM_REPOS, []):
        repo_id = slug_to_repo_id(slug, augur)
        if repo_id is not None:
            values.append(str(repo_id))
        else:
            unknown_slugs.append(slug)
            logging.warning(f"URL_STATE: slug not found in Augur: {slug!r}")

    for org in parsed.get(PARAM_ORGS, []):
        if augur.is_org(org):
            values.append(org)
        else:
            unknown_slugs.append(org)
            logging.warning(f"URL_STATE: org not found in Augur: {org!r}")

    return values, unknown_slugs
