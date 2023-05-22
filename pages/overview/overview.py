from dash import html, dcc
import dash
import dash_bootstrap_components as dbc

# import the visualization cards
from .visualizations.commits_over_time import gc_commits_over_time
from .visualizations.issues_over_time import gc_issues_over_time

# disable and re-enable formatter
# fmt: off
from .visualizations.active_drifting_contributors import gc_active_drifting_contributors
from .visualizations.new_contributor import gc_new_contributor
# fmt: on
from .visualizations.issue_staleness import gc_issue_staleness
from .visualizations.pr_staleness import gc_pr_staleness
from .visualizations.pr_over_time import gc_pr_over_time


# register the page
dash.register_page(__name__, path="/overview", order=2)

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_active_drifting_contributors, width=6),
                dbc.Col(gc_new_contributor, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_pr_staleness, width=6),
                dbc.Col(gc_pr_over_time, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_issue_staleness, width=6),
                dbc.Col(gc_issues_over_time, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_commits_over_time, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
