from dash import html
import dash
import dash_bootstrap_components as dbc
from .visualizations.commit_metrics import gc_commit_metrics
from .visualizations.pr_metrics import gc_pr_metrics
from .visualizations.issue_metrics import gc_issue_metrics

# register the page
# dash.register_page(__name__, path="/", order=1)

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H1(children="At a Glance")),
        ),
        dbc.Row(gc_commit_metrics),
        dbc.Row(gc_issue_metrics),
        dbc.Row(gc_pr_metrics),
        dbc.Row(
            [
                html.H4(
                    "Looking for more information on definitions and how to use the app? See the info tab",
                ),
            ],
            align="baseline",
        ),
    ],
    fluid=True,
)
