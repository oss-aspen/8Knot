import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cache_manager.url_state import encode_state, decode_state, CURRENT_VERSION


def test_round_trip_basic():
    encoded = encode_state([42, 107], ["apache"], "/contributions", "pr-staleness")
    decoded = decode_state(encoded)
    assert decoded is not None
    assert decoded["v"] == CURRENT_VERSION
    assert decoded["repo_ids"] == [42, 107]
    assert decoded["org_names"] == ["apache"]
    assert decoded["pathname"] == "/contributions"
    assert decoded["graph_id"] == "pr-staleness"
    assert decoded["filters"] == {}


def test_round_trip_with_filters():
    filters = {"date_range": 365, "bot_filter": True}
    encoded = encode_state([1], [], "/chaoss", "lottery-factor", filters)
    decoded = decode_state(encoded)
    assert decoded["filters"] == filters


def test_round_trip_large_payload():
    repo_ids = list(range(200))
    encoded = encode_state(repo_ids, ["org" * 20] * 5, "/contributions", "pr-staleness")
    assert len(encoded) < 2000
    decoded = decode_state(encoded)
    assert decoded["repo_ids"] == repo_ids


def test_round_trip_null_graph_id():
    encoded = encode_state([1, 2], [], "/contributions", None)
    decoded = decode_state(encoded)
    assert decoded["graph_id"] is None


def test_decode_invalid_input():
    assert decode_state("") is None
    assert decode_state("not-valid-base64!!!") is None
    assert decode_state("AAAA") is None


def test_decode_wrong_version():
    import json, gzip, base64

    payload = {"v": 999, "repo_ids": [1], "org_names": [], "pathname": "/", "graph_id": None, "filters": {}}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    compressed = gzip.compress(raw)
    encoded = base64.urlsafe_b64encode(compressed).decode().rstrip("=")
    assert decode_state(encoded) is None


def test_encode_is_url_safe():
    encoded = encode_state([1, 2, 3], ["test"], "/contributions", "pr-staleness")
    assert "+" not in encoded
    assert "/" not in encoded
    assert "=" not in encoded


if __name__ == "__main__":
    test_round_trip_basic()
    test_round_trip_with_filters()
    test_round_trip_large_payload()
    test_round_trip_null_graph_id()
    test_decode_invalid_input()
    test_decode_wrong_version()
    test_encode_is_url_safe()
    print("All url_state tests passed")
