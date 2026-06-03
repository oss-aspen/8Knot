from __future__ import annotations

import secrets
import string
import logging
import random

ALPHABET = string.ascii_letters + string.digits
MAX_SHORT_ID_LEN = 12
_CLEANUP_PROBABILITY = 0.02


def _gen_id(length=8) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def shorten(conn, full_state: str, max_attempts: int = 3) -> str:
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
    conn.commit()
    raise RuntimeError("Failed to generate unique short_id after retries")


def expand(conn, short_id: str) -> str | None:
    if not short_id or len(short_id) > MAX_SHORT_ID_LEN:
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
