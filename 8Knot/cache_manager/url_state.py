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
            return None
        return payload
    except Exception:
        return None
