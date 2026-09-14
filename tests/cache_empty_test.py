"""Run with PYTHONPATH=8Knot python -B -m unittest discover -s tests -p '*_test.py' -v."""

import os
import sys
import unittest
import warnings
from copy import deepcopy
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from celery import Celery
from dash.background_callback.managers import BaseBackgroundCallbackManager
from dash.development.base_component import ComponentRegistry
from sqlalchemy.exc import SQLAlchemyError


TEST_ENV = {
    "AUGUR_USERNAME": "test",
    "AUGUR_PASSWORD": "test",
    "AUGUR_HOST": "invalid",
    "AUGUR_PORT": "5432",
    "AUGUR_DATABASE": "test",
}

with patch.dict(os.environ, TEST_ENV):
    import cache_manager.cache_facade as cf
    from db_manager.augur_manager import AugurManager
    import _bots
    from pages.utils import job_utils


class CacheFacadeTests(unittest.TestCase):
    def setUp(self):
        connection = patch.object(cf.pg, "connect")
        self.connect = connection.start()
        self.addCleanup(connection.stop)
        self.cursor = self.connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value

    def test_empty_selection_skips_database_and_cache_fill(self):
        self.assertEqual(cf.get_uncached("query", []), [])
        with patch.object(cf, "cache_query_results") as fill:
            cf.caching_wrapper("query", "SELECT", [])
        self.connect.assert_not_called()
        fill.assert_not_called()

    def test_cached_selection_skips_cache_fill(self):
        self.cursor.fetchall.return_value = [(11,)]
        with patch.object(cf, "cache_query_results") as fill:
            cf.caching_wrapper("query", "SELECT", [11])
        fill.assert_not_called()

    def test_mixed_selection_records_only_missing_repositories(self):
        self.cursor.fetchall.return_value = [(11,), (11,)]
        for repetitions in (1, 2):
            with self.subTest(repetitions=repetitions), patch.object(cf, "cache_query_results") as fill:
                cf.caching_wrapper("query", "SELECT", [11, 22, 22, 33], n_repolist_uses=repetitions)
                fill.assert_called_once()
                arguments = fill.call_args.kwargs
                self.assertEqual(len(arguments["vars"]), repetitions)
                for ids in arguments["vars"]:
                    self.assertEqual(set(ids), {22, 33})
                records = arguments["bookkeeping_data"]
                self.assertEqual(len(records), 2)
                self.assertEqual({row["repo_id"] for row in records}, {22, 33})
                self.assertTrue(all(row["cache_func"] == "query" for row in records))
        self.assertEqual(self.cursor.execute.call_args.kwargs["vars"], ((11, 22, 22, 33),))

    def test_cache_reads_preserve_columns_for_empty_and_nonempty_selections(self):
        self.cursor.description = [("repo_id",), ("message",)]
        for repos, parameters, rows in [([], ((None,),), []), ([11], ((11,),), [(11, "value")])]:
            with self.subTest(repos=repos):
                self.cursor.fetchall.return_value = rows
                result = cf.retrieve_from_cache("query", repos)
                self.assertEqual(self.cursor.execute.call_args.args[1], parameters)
                pd.testing.assert_frame_equal(result, pd.DataFrame(rows, columns=["repo_id", "message"]))


class AugurManagerTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, TEST_ENV):
            self.manager = AugurManager()
        self.manager.engine = MagicMock()

    def test_query_errors_retain_cause_and_traceback(self):
        for stage in ("connect", "read"):
            with self.subTest(stage=stage):
                original = SQLAlchemyError("query failed")
                self.manager.engine.connect.side_effect = original if stage == "connect" else None
                with patch.object(pd, "read_sql", side_effect=original), self.assertLogs(level="ERROR") as logs:
                    with self.assertRaises(Exception) as raised:
                        self.manager.run_query("SELECT 1")
                self.assertEqual(str(raised.exception), "DB Read Failure")
                self.assertIs(raised.exception.__cause__, original)
                self.assertIs(logs.records[0].exc_info[1], original)

    def test_process_control_exceptions_propagate_unchanged(self):
        for original in (KeyboardInterrupt(), SystemExit(3)):
            with self.subTest(exception=type(original).__name__):
                self.manager.engine.connect.side_effect = original
                with self.assertRaises(type(original)) as raised:
                    self.manager.run_query("SELECT 1")
                self.assertIs(raised.exception, original)

    def test_successful_query_preserves_data_and_resets_index(self):
        frame = pd.DataFrame({"repo_id": [11]}, index=[5])
        with patch.object(pd, "read_sql", return_value=frame):
            result = self.manager.run_query("SELECT repo_id")
        pd.testing.assert_frame_equal(result, frame.reset_index(drop=True))


class BotStartupTests(unittest.TestCase):
    def test_initialization_failures_propagate_unchanged(self):
        for stage, original in [("init", KeyError("AUGUR_HOST")), ("engine", SQLAlchemyError("offline"))]:
            with self.subTest(stage=stage), patch.object(_bots, "AugurManager") as constructor:
                if stage == "init":
                    constructor.side_effect = original
                else:
                    constructor.return_value.get_engine.side_effect = original
                with self.assertLogs(level="ERROR"), self.assertRaises(type(original)) as raised:
                    _bots.get_bots_list()
                self.assertIs(raised.exception, original)
                constructor.return_value.run_query.assert_not_called()

    def test_successful_bot_query_preserves_id_format(self):
        with patch.object(_bots, "AugurManager") as constructor:
            constructor.return_value.run_query.return_value = pd.DataFrame({"cntrb_id": [123, 1234567890123456]})
            self.assertEqual(_bots.get_bots_list(), ["123", "123456789012345"])


class EmptySelectionCallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Avoid app.py's database connections and worker setup while importing real callbacks.
        app = ModuleType("app")
        app.augur = Mock(spec=AugurManager)
        app.augur.repo_id_to_git.side_effect = lambda repo: f"repo-{repo}"
        app.bots_list = []
        app.celery_app = Celery("cache-tests", broker="memory://", backend="cache+memory://", set_as_current=False)
        cls.addClassCleanup(app.celery_app.close)
        with (
            patch.object(BaseBackgroundCallbackManager, "managers", []),
            patch.object(BaseBackgroundCallbackManager, "functions", []),
        ):
            cls.existing_manager = dash.CeleryManager(app.celery_app)
            # Restore registrations alongside modules, including those sent to existing managers.
            with (
                warnings.catch_warnings(),
                patch.object(ComponentRegistry, "registry", deepcopy(ComponentRegistry.registry)),
                patch.object(ComponentRegistry, "namespace_to_package", ComponentRegistry.namespace_to_package.copy()),
                patch.object(ComponentRegistry, "children_props", deepcopy(ComponentRegistry.children_props)),
                patch("dash._callback.GLOBAL_CALLBACK_MAP", {}),
                patch("dash._callback.GLOBAL_CALLBACK_LIST", []),
                patch.object(BaseBackgroundCallbackManager, "managers", []),
                patch.object(BaseBackgroundCallbackManager, "functions", []),
                patch.dict(sys.modules, {"app": app}),
                patch("dash.register_page"),
            ):
                from pages.codebase.visualizations import (
                    cntrb_file_heatmap,
                    contribution_file_heatmap,
                    reviewer_file_heatmap,
                )
                from pages.repo_overview import repo_overview
                from pages.repo_overview.visualizations import ossf_scorecard, repo_general_info
            cls.background_functions_after_import = list(BaseBackgroundCallbackManager.functions)

        cls.heatmaps = (cntrb_file_heatmap, contribution_file_heatmap, reviewer_file_heatmap)
        cls.overview = repo_overview
        cls.scorecard = ossf_scorecard
        cls.general_info = repo_general_info

    def test_callback_imports_do_not_break_other_apps(self):
        with patch("dash._callback.GLOBAL_CALLBACK_MAP", {}), patch("dash._callback.GLOBAL_CALLBACK_LIST", []):
            app = dash.Dash(__name__)
            app.layout = dash.html.Div("Ready")
            self.assertEqual(app.server.test_client().get("/").status_code, 200)

    def test_callback_imports_preserve_existing_background_managers(self):
        self.assertEqual(self.background_functions_after_import, [])
        self.assertEqual(self.existing_manager.func_registry, {})

    def test_empty_callbacks_do_not_query_the_cache(self):
        with (
            patch.object(cf, "get_uncached", side_effect=AssertionError("unexpected cache poll")),
            patch.object(cf, "retrieve_from_cache", side_effect=AssertionError("unexpected cache read")),
        ):
            with self.subTest(callback="get_default_repo_with_data"):
                self.assertIsNone(job_utils.get_default_repo_with_data([], "query"))
            with self.subTest(callback="repo_overview.repo_dropdown"):
                self.assertEqual(self.overview.repo_dropdown([]), ([], None))
            for module in self.heatmaps:
                with self.subTest(module=module.__name__):
                    self.assertEqual(module.repo_dropdown([]), ([], None))
                    self.assertEqual(module.directory_dropdown(None), ([], None))
            graph_calls = [
                (self.heatmaps[0].cntrb_file_heatmap_graph, ([], None, None, False)),
                (self.heatmaps[1].cntrb_file_heatmap_graph, (None, None, "created_at")),
                (self.heatmaps[2].reviewer_file_heatmap_graph, ([], None, None, False)),
            ]
            for callback, arguments in graph_calls:
                with self.subTest(callback=callback.__module__):
                    self.assertIs(callback(*arguments), job_utils.nodata_graph)
            for callback in (self.scorecard.ossf_scorecard, self.general_info.repo_general_info):
                with self.subTest(callback=callback.__name__):
                    table, label = callback(None)
                    self.assertIsInstance(table, dbc.Table)
                    self.assertEqual(label.children, "No data")

    def test_default_repository_preserves_selection_order_and_fallback(self):
        for cached_ids, expected in [([], "22"), ([11, 22], "22"), ([11], "11")]:
            with (
                self.subTest(cached_ids=cached_ids),
                patch.object(cf, "retrieve_from_cache", return_value=pd.DataFrame({"repo_id": cached_ids})),
            ):
                self.assertEqual(job_utils.get_default_repo_with_data([22, 11], "query"), expected)

    def test_repository_dropdowns_can_clear_and_reselect(self):
        choices = [{"value": "22", "label": "repo-22"}, {"value": "11", "label": "repo-11"}]
        for module in (*self.heatmaps, self.overview):
            with (
                self.subTest(module=module.__name__),
                patch.object(cf, "retrieve_from_cache", return_value=pd.DataFrame({"repo_id": [22]})),
            ):
                self.assertEqual(module.repo_dropdown([22, 11]), (choices, "22"))
                self.assertEqual(module.repo_dropdown([]), ([], None))
                self.assertEqual(module.repo_dropdown([22, 11]), (choices, "22"))

    def test_directory_dropdowns_can_clear_and_reselect(self):
        for module in self.heatmaps:
            with (
                self.subTest(module=module.__name__),
                patch.object(cf, "get_uncached", return_value=[]),
                patch.object(cf, "retrieve_from_cache", return_value=pd.DataFrame()) as read,
            ):
                expected = (["Top Level Directory"], "Top Level Directory")
                self.assertEqual(module.directory_dropdown("22"), expected)
                self.assertEqual(module.directory_dropdown(None), ([], None))
                self.assertEqual(module.directory_dropdown("22"), expected)
                self.assertEqual(read.call_count, 2)
                self.assertEqual(read.call_args.kwargs["repolist"], [22])


if __name__ == "__main__":
    unittest.main()
