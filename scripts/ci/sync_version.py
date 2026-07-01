#!/usr/bin/env python3
"""
sync_version.py: Regenerate 8Knot/_version.py from the version in pyproject.toml.

pyproject.toml is the single source of truth for the release version. This keeps
the runtime constant in 8Knot/_version.py in sync so the app can import it without
reading pyproject.toml at runtime (it isn't available in the container). Run as a
pre-commit hook; exits non-zero when it rewrites the file so the change is staged.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
VERSION_FILE = ROOT / "8Knot" / "_version.py"

TEMPLATE = '''\
"""Release version for 8Knot. Auto-generated from pyproject.toml by scripts/ci/sync_version.py — edit pyproject.toml, not this file."""

__version__ = "{version}"
'''


def main() -> int:
    match = re.search(r'^version\s*=\s*"([^"]+)"', PYPROJECT.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        print("ERROR: could not find a version in pyproject.toml", file=sys.stderr)
        return 1

    content = TEMPLATE.format(version=match.group(1))
    if not VERSION_FILE.exists() or VERSION_FILE.read_text(encoding="utf-8") != content:
        VERSION_FILE.write_text(content, encoding="utf-8")
        print(f"Updated 8Knot/_version.py to {match.group(1)} — re-stage and commit.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
