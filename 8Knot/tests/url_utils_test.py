import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pages.utils.url_utils import (
    extract_url_params,
    extract_base_url,
    compose_short_url,
    compose_long_url,
    validate_target,
    VALID_GRAPH_REGISTRY,
)


def test_extract_base_url_basic():
    assert extract_base_url("https://8knot.example.com/contributions?s=abc#g") == "https://8knot.example.com"


def test_extract_base_url_path_collision():
    # hostname contains a path-like substring — slicing on pathname would break
    assert extract_base_url("https://contributions.8knot.io/contributions?x=1") == "https://contributions.8knot.io"


def test_extract_base_url_with_port():
    assert extract_base_url("http://localhost:8050/repo_overview") == "http://localhost:8050"


def test_extract_base_url_empty():
    assert extract_base_url("") == "://"
    assert extract_base_url(None) == "://"


def test_extract_short_id():
    params = extract_url_params("?s=a3Kz9mPq")
    assert params["short_id"] == "a3Kz9mPq"
    assert params["state"] is None


def test_extract_state():
    params = extract_url_params("?state=H4sIAAAA")
    assert params["state"] == "H4sIAAAA"
    assert params["short_id"] is None


def test_extract_empty():
    assert extract_url_params("") == {}
    assert extract_url_params(None) == {}


def test_extract_both_params():
    params = extract_url_params("?s=abc&state=xyz")
    assert params["short_id"] == "abc"
    assert params["state"] == "xyz"


def test_compose_short_url():
    url = compose_short_url("https://8knot.example.com", "a3Kz9mPq", "/contributions", "pr-staleness")
    assert url == "https://8knot.example.com/contributions?s=a3Kz9mPq#pr-staleness"


def test_compose_short_url_no_graph():
    url = compose_short_url("https://8knot.example.com", "abc123", "/contributions", None)
    assert url == "https://8knot.example.com/contributions?s=abc123"


def test_compose_short_url_trailing_slash():
    url = compose_short_url("https://8knot.example.com/", "abc", "/chaoss", "lottery-factor")
    assert url == "https://8knot.example.com/chaoss?s=abc#lottery-factor"


def test_compose_long_url():
    url = compose_long_url("https://8knot.example.com", "H4sIAAAA", "/contributions", "pr-staleness")
    assert url == "https://8knot.example.com/contributions?state=H4sIAAAA#pr-staleness"


def test_validate_target_valid():
    for pathname in VALID_GRAPH_REGISTRY:
        is_valid, redirect = validate_target(pathname, None)
        assert is_valid is True
        assert redirect is None


def test_validate_target_invalid():
    is_valid, redirect = validate_target("/nonexistent-page", None)
    assert is_valid is False
    assert redirect is None


def test_validate_target_deprecated():
    from pages.utils.url_utils import DEPRECATED_GRAPH_REGISTRY

    # Only runs if there are deprecated entries
    if DEPRECATED_GRAPH_REGISTRY:
        key = next(iter(DEPRECATED_GRAPH_REGISTRY))
        is_valid, redirect = validate_target(key[0], key[1])
        assert is_valid is False
        assert redirect is not None


if __name__ == "__main__":
    test_extract_base_url_basic()
    test_extract_base_url_path_collision()
    test_extract_base_url_with_port()
    test_extract_base_url_empty()
    test_extract_short_id()
    test_extract_state()
    test_extract_empty()
    test_extract_both_params()
    test_compose_short_url()
    test_compose_short_url_no_graph()
    test_compose_short_url_trailing_slash()
    test_compose_long_url()
    test_validate_target_valid()
    test_validate_target_invalid()
    test_validate_target_deprecated()
    print("All url_utils tests passed")
