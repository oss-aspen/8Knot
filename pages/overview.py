from dash import html, dcc
import dash
import dash_bootstrap_components as dbc

# import the visualization cards
from .visualizations.overview.commits_over_time import gc_commits_over_time
from .visualizations.overview.issues_over_time import gc_issues_over_time

# disable and re-enable formatter
# fmt: off
from .visualizations.overview.active_drifting_contributors import gc_active_drifting_contributors
from .visualizations.overview.total_contributor_growth import gc_total_contributor_growth
# fmt: on
from .visualizations.overview.issue_staleness import gc_issue_staleness
from .visualizations.overview.pr_staleness import gc_pr_staleness
from .visualizations.overview.pr_over_time import gc_pr_over_time


# register the page
dash.register_page(__name__, order=2)

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H1(children="Overview")),
        ),
        dbc.Row(
            [
                dbc.Col(gc_issues_over_time, width=6),
                dbc.Col(gc_commits_over_time, width=6),
            ],
            align="center",
            style={"margin-bottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_total_contributor_growth, width=6),
                dbc.Col(gc_active_drifting_contributors, width=6),
            ],
            align="center",
            style={"margin-bottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_issue_staleness, width=6),
                dbc.Col(gc_pr_staleness, width=6),
            ],
            align="center",
            style={"margin-bottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_pr_over_time, width=6),
            ],
            align="center",
            style={"margin-bottom": ".5%"},
        ),
    ],
    fluid=True,
)
