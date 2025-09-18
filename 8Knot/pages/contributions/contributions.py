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
            gc_pr_staleness,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_pr_over_time,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_cntrib_pr_assignment,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_pr_assignment,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_issue_staleness,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_issues_over_time,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_cntrib_issue_assignment,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_issue_assignment,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_commits_over_time,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_pr_first_response,
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            gc_pr_review_response,
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
