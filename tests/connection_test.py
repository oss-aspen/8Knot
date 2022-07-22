# from explorer.db_interface.AugurInterface import AugurInterface
import pytest


class TestDatabaseConnection:
    def test_get_augur_db(self):
        assert "hello" == "hello"

    def test_get_engine(self):
        assert "world" == "world"

    @pytest.mark.skip("testing skip")
    def test_get_connection(self):
        assert "hello" == "world"

    @pytest.mark.xfail
    def test_get_faulty_connection(self):
        assert 1 == 2
