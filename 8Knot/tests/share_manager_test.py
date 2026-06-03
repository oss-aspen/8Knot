import sys
import os
import sqlite3
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cache_manager.share_manager import _gen_id, shorten, expand, MAX_SHORT_ID_LEN


def test_gen_id_length():
    assert len(_gen_id(8)) == 8
    assert len(_gen_id(12)) == 12


def test_gen_id_charset():
    import string

    valid = set(string.ascii_letters + string.digits)
    for _ in range(100):
        id_ = _gen_id()
        assert all(c in valid for c in id_)


def test_expand_rejects_oversized_input():
    conn = MagicMock()
    assert expand(conn, "x" * (MAX_SHORT_ID_LEN + 1)) is None
    conn.cursor.assert_not_called()


def test_expand_rejects_empty_input():
    conn = MagicMock()
    assert expand(conn, "") is None
    assert expand(conn, None) is None


def _make_mock_conn(rowcount=1, fetchone_result=None):
    conn = MagicMock()
    cur = MagicMock()
    cur.rowcount = rowcount
    cur.fetchone.return_value = fetchone_result
    cur.__enter__ = lambda self: self
    cur.__exit__ = lambda self, *a: None
    conn.cursor.return_value = cur
    return conn, cur


def test_shorten_returns_id_on_success():
    conn, cur = _make_mock_conn(rowcount=1)
    result = shorten(conn, "some_state_blob")
    assert len(result) == 8
    conn.commit.assert_called()


def test_shorten_retries_on_collision():
    conn = MagicMock()
    cur = MagicMock()
    cur.rowcount = 0
    cur.__enter__ = lambda self: self
    cur.__exit__ = lambda self, *a: None
    conn.cursor.return_value = cur

    try:
        shorten(conn, "state", max_attempts=3)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "unique short_id" in str(e)


def test_expand_returns_state():
    conn, cur = _make_mock_conn(fetchone_result=("encoded_state_blob",))
    result = expand(conn, "abc12345")
    assert result == "encoded_state_blob"
    conn.commit.assert_called()


def test_expand_returns_none_for_missing():
    conn, cur = _make_mock_conn(fetchone_result=None)
    result = expand(conn, "notfound1")
    assert result is None


if __name__ == "__main__":
    test_gen_id_length()
    test_gen_id_charset()
    test_expand_rejects_oversized_input()
    test_expand_rejects_empty_input()
    test_shorten_returns_id_on_success()
    test_shorten_retries_on_collision()
    test_expand_returns_state()
    test_expand_returns_none_for_missing()
    print("All share_manager tests passed")
