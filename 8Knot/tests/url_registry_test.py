"""
Drift guard for VALID_GRAPH_REGISTRY.

The registry in ``pages/utils/url_utils.py`` enumerates the valid
(pathname, graph_id) pairs used to validate shared links. The graph IDs it
lists must match the real ``VIZ_ID`` of every visualization actually rendered
on each page — those are the IDs share buttons emit.

This test re-derives that mapping straight from the source (each page layout's
``register_page`` path + the viz modules it imports + each module's VIZ_ID) and
asserts it equals the registry. If a graph is added, removed, or renamed and
the registry isn't updated, this fails in CI — so the second source of truth
can't silently drift.

It parses source as plain text (no dash import), so it runs fast and without
the app's runtime dependencies.
"""

import os
import re
import glob
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pages.utils.url_utils import VALID_GRAPH_REGISTRY

_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _viz_id_by_module():
    """module basename -> VIZ_ID for every visualization module."""
    out = {}
    for f in glob.glob(os.path.join(_ROOT, "pages", "**", "visualizations", "*.py"), recursive=True):
        src = open(f, encoding="utf-8").read()
        m = re.search(r'^VIZ_ID\s*=\s*["\']([^"\']+)', src, re.M)
        if m:
            out[os.path.splitext(os.path.basename(f))[0]] = m.group(1)
    return out


def _derive_registry():
    """Rebuild pathname -> sorted[viz_id] from the live page layouts."""
    viz_by_module = _viz_id_by_module()
    derived = {}
    for f in glob.glob(os.path.join(_ROOT, "pages", "**", "*.py"), recursive=True):
        src = open(f, encoding="utf-8").read()
        page = re.search(r'register_page\([^)]*path\s*=\s*["\']([^"\']+)', src)
        if not page:
            continue
        mods = re.findall(r"from\s+\.visualizations\.(\w+)\s+import", src)
        vids = sorted({viz_by_module[m] for m in mods if m in viz_by_module})
        if vids:
            derived[page.group(1)] = vids
    return derived


def test_registry_matches_live_pages():
    derived = _derive_registry()
    assert derived, "no viz pages discovered — derivation logic or paths are wrong"

    registry = {path: sorted(graphs) for path, graphs in VALID_GRAPH_REGISTRY.items()}
    assert registry == derived, (
        "VALID_GRAPH_REGISTRY is out of sync with the live visualization pages.\n"
        f"Derived from pages: {derived}\n"
        f"Registry:           {registry}"
    )


def test_registry_pathnames_are_absolute():
    for pathname in VALID_GRAPH_REGISTRY:
        assert pathname.startswith("/"), f"registry pathname not absolute: {pathname}"


if __name__ == "__main__":
    test_registry_matches_live_pages()
    test_registry_pathnames_are_absolute()
    print("All url_registry tests passed")
