"""
Drift guard for VALID_GRAPH_REGISTRY.

The sidebar navigation in `pages/index/index_components.py` and the
`VALID_GRAPH_REGISTRY` in `pages/utils/url_utils.py` both enumerate the
valid (pathname, graph_id) pairs. That is a second source of truth, so this
test asserts the registry recognizes every graph the sidebar links to —
catching drift in CI before a stale registry silently rejects a real
shared link.

It reads the sidebar module as plain text (no dash import needed), so it
runs fast and without the app's runtime dependencies.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pages.utils.url_utils import VALID_GRAPH_REGISTRY

_SIDEBAR_SRC = os.path.join(os.path.dirname(__file__), "..", "pages", "index", "index_components.py")

# Matches sidebar hrefs like "/contributions#commits-over-time".
_HREF_RE = re.compile(r'"(/[\w/]+)#([\w-]+)"')


def _sidebar_targets():
    with open(_SIDEBAR_SRC, encoding="utf-8") as fh:
        source = fh.read()
    return _HREF_RE.findall(source)


def test_sidebar_targets_exist_in_registry():
    targets = _sidebar_targets()
    assert targets, "no sidebar hrefs found — regex or source path is wrong"

    drift = []
    for pathname, graph_id in targets:
        graphs = VALID_GRAPH_REGISTRY.get(pathname)
        if graphs is None or graph_id not in graphs:
            drift.append((pathname, graph_id))

    assert not drift, "VALID_GRAPH_REGISTRY is out of sync with the sidebar navigation. " f"Missing entries: {drift}"


def test_registry_pathnames_are_absolute():
    for pathname in VALID_GRAPH_REGISTRY:
        assert pathname.startswith("/"), f"registry pathname not absolute: {pathname}"


if __name__ == "__main__":
    test_sidebar_targets_exist_in_registry()
    test_registry_pathnames_are_absolute()
    print("All url_registry tests passed")
