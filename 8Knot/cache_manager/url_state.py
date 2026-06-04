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


def decode_state(encoded: str) -> dict | None:
    try:
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
            return _migrate(payload)
        return payload
    except Exception:
        return None
