from __future__ import annotations

import io
import gzip
import json
import base64

CURRENT_VERSION = 1

# Upper bound on the decompressed payload. The `?state=` blob is fully
# attacker-controlled and gzip.decompress is otherwise unbounded, so a tiny
# crafted string could expand to gigabytes (a "zip bomb") and exhaust memory.
# 64 KiB is far larger than any legitimate state (a 200-repo payload is < 1 KiB
# decompressed) while making the DoS vector harmless.
MAX_DECODED_BYTES = 64 * 1024

# Upper bound on the ENCODED (?state=) string itself, checked before any work.
# A legitimate 200-repo link is < 1 KiB; 16 KiB is generous headroom. This makes
# decode self-contained instead of relying on the web server's request-line cap.
MAX_ENCODED_LEN = 16 * 1024

# Hard caps on collection sizes inside a decoded payload. Bounds the work done
# resolving a crafted link even though the 64 KiB output cap already limits it.
_MAX_REPO_IDS = 10_000
_MAX_ORG_NAMES = 1_000


# Migration registry: maps an OLD payload version -> a function that upgrades a
# decoded payload by exactly one version (v -> v+1, bumping the "v" field).
# `decode_state` walks this chain so links encoded by an older app version keep
# resolving after a CURRENT_VERSION bump, instead of every short link breaking
# at once. This is the single place to add upgrade logic when the schema
# changes — e.g. when bumping to v2:
#
#     def _v1_to_v2(p):
#         p["filters"].setdefault("bot_filter", True)
#         p["v"] = 2
#         return p
#     MIGRATIONS = {1: _v1_to_v2}
#
# The upgrade happens in memory on read, so stored DB rows never need a
# migration of their own.
MIGRATIONS: dict = {}


def _migrate(payload: dict) -> dict | None:
    """Upgrade a decoded payload to CURRENT_VERSION, or None if no path exists."""
    v = payload.get("v")
    while v != CURRENT_VERSION:
        migrate = MIGRATIONS.get(v)
        if migrate is None:
            return None  # no registered upgrade from this version
        payload = migrate(payload)
        new_v = payload.get("v")
        if new_v == v:  # guard: a migration that fails to advance would loop forever
            return None
        v = new_v
    return payload


def encode_state(
    repo_ids: list[int], org_names: list[str], pathname: str, graph_id: str | None, filters: dict | None = None
) -> str:
    payload = {
        "v": CURRENT_VERSION,
        "repo_ids": repo_ids,
        "org_names": org_names,
        "pathname": pathname,
        "graph_id": graph_id,
        "filters": filters or {},
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    compressed = gzip.compress(raw, compresslevel=9)
    return base64.urlsafe_b64encode(compressed).decode().rstrip("=")


def _is_valid_shape(p: dict) -> bool:
    """Validate the decoded payload's field types.

    The ``?state=`` blob is fully attacker-controlled, so a structurally valid
    JSON object can still carry hostile shapes (e.g. ``pathname`` as a list, or
    ``repo_ids`` holding unhashable values) that would raise unhandled
    TypeErrors in downstream lookups. Rejecting bad shapes here means every
    consumer can trust the payload. ``bool`` is excluded from ints because
    ``isinstance(True, int)`` is True in Python.
    """
    if not isinstance(p.get("pathname"), str):
        return False
    gid = p.get("graph_id")
    if gid is not None and not isinstance(gid, str):
        return False
    repo_ids = p.get("repo_ids", [])
    if not isinstance(repo_ids, list) or len(repo_ids) > _MAX_REPO_IDS:
        return False
    if not all(isinstance(r, int) and not isinstance(r, bool) for r in repo_ids):
        return False
    org_names = p.get("org_names", [])
    if not isinstance(org_names, list) or len(org_names) > _MAX_ORG_NAMES:
        return False
    if not all(isinstance(o, str) for o in org_names):
        return False
    if not isinstance(p.get("filters", {}), dict):
        return False
    return True


def decode_state(encoded: str) -> dict | None:
    try:
        if not encoded or len(encoded) > MAX_ENCODED_LEN:
            return None

        padded = encoded + "=" * (-len(encoded) % 4)
        compressed = base64.urlsafe_b64decode(padded)

        # Bounded read: pull at most MAX_DECODED_BYTES + 1 so we can detect (and
        # reject) anything larger without ever materializing the full bomb.
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as f:
            raw = f.read(MAX_DECODED_BYTES + 1)
        if len(raw) > MAX_DECODED_BYTES:
            return None

        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return None
        if payload.get("v") != CURRENT_VERSION:
            # Old-format link: try to upgrade it in memory rather than reject.
            payload = _migrate(payload)
            if payload is None:
                return None
        # Type-validate the (possibly migrated) payload so consumers can trust it.
        if not _is_valid_shape(payload):
            return None
        return payload
    except Exception:
        return None
