from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import the visualization cards
from .visualizations.commits_over_time import gc_commits_over_time
from .visualizations.issues_over_time import gc_issues_over_time
from .visualizations.issue_staleness import gc_issue_staleness
from .visualizations.pr_staleness import gc_pr_staleness
from .visualizations.pr_over_time import gc_pr_over_time
from .visualizations.self_merge_rate import gc_self_merge
from .visualizations.cntrib_issue_assignment import gc_cntrib_issue_assignment
from .visualizations.issue_assignment import gc_issue_assignment
from .visualizations.pr_assignment import gc_pr_assignment
from .visualizations.cntrb_pr_assignment import gc_cntrib_pr_assignment
from .visualizations.pr_first_response import gc_pr_first_response
from .visualizations.pr_review_response import gc_pr_review_response

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/contributions")

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                dbc.Alert(
                    "Contribution visualizations group commits, issues, pull requests, reviews, and response-time metrics for the selected repositories.",
                    color="secondary",
                    className="mb-3",
                ),
                xl=10,
            ),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_commits_over_time, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_pr_over_time, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_pr_staleness, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_self_merge, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_pr_first_response, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_pr_review_response, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_pr_assignment, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_cntrib_pr_assignment, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_issues_over_time, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_issue_staleness, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_issue_assignment, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_cntrib_issue_assignment, xl=10),
            className="visualization-row",
        ),
    ],
    fluid=True,
)
