from __future__ import annotations

import secrets
import string
import logging
import random

# base62 ids from a cryptographic RNG -> unguessable, URL-safe.
ALPHABET = string.ascii_letters + string.digits
_ALPHABET_SET = set(ALPHABET)
MAX_SHORT_ID_LEN = 12

# Hard cap on a stored blob. encode_state output is already bounded by the
# searchbar selection, but this stops a crafted/oversized write from bloating
# the shared table. 64 KiB matches the decode-side decompression cap.
MAX_STATE_LEN = 64 * 1024

_CLEANUP_PROBABILITY = 0.02


def _gen_id(length: int = 8) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def shorten(conn, full_state: str, max_attempts: int = 3) -> str:
    """Store a state blob and return an unguessable short id.

    Raises ValueError on an empty/oversized blob and RuntimeError if a unique
    id can't be generated (astronomically unlikely with a 62^8 keyspace).
    """
    if not full_state or len(full_state) > MAX_STATE_LEN:
        raise ValueError("share state blob is empty or exceeds the maximum size")

    for _ in range(max_attempts):
        short_id = _gen_id()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO share_links (short_id, full_state)
                   VALUES (%s, %s)
                   ON CONFLICT (short_id) DO NOTHING""",
                (short_id, full_state),
            )
            if cur.rowcount == 1:
                conn.commit()
                if random.random() < _CLEANUP_PROBABILITY:
                    _try_cleanup(conn)
                return short_id
    # Every attempt collided. Nothing was written, so there is nothing to
    # commit — just surface the failure.
    raise RuntimeError("Failed to generate unique short_id after retries")


def expand(conn, short_id: str) -> str | None:
    """Return the stored blob for a valid, non-expired id, else None.

    Validates the id shape (length + base62 charset) before touching the DB so
    a malformed/oversized value never reaches a query. SQL is parameterized, so
    even an odd value can't inject — this is defense in depth and load-shedding.
    """
    if not short_id or len(short_id) > MAX_SHORT_ID_LEN or not _ALPHABET_SET.issuperset(short_id):
        return None
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE share_links
               SET last_accessed = NOW(), access_count = access_count + 1
               WHERE short_id = %s AND expires_at > NOW()
               RETURNING full_state""",
            (short_id,),
        )
        row = cur.fetchone()
    conn.commit()
    return row[0] if row else None


def cleanup_expired(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM share_links WHERE expires_at <= NOW()")
        count = cur.rowcount
    conn.commit()
    return count


def _try_cleanup(conn) -> None:
    try:
        removed = cleanup_expired(conn)
        if removed:
            logging.info(f"share_manager: cleaned up {removed} expired links")
    except Exception as e:
        logging.warning(f"share_manager: cleanup failed: {e}")
