"""HOMEPAGE DOCSTRING

Page is pending overhaul.

Single-value metrics like those currently represented aren't very useful, and feedback has
largely been that this page should say nothing rather than mis-represent project behavior.
These metrics currently capture the all-time behavior of a group of projects and say *something* without
being informative.

For example: {# lines added in all commits for all time} says nothing about the
kind of contributions those lines were for, whether documentation or code. They aren't
good proxies for churn, because they're not isolated to any period of time.

Another example: {Avg. lifespan of PRs that have been merged for all time} is heavily skewed
by events like rubber-stamp merges at the beginning of a project's life, or extremely large overhauls
that take a long time to merge. It would be more useful to describe the IQR over time, binning the
lifespans and considering outliers independently.

Page will not be registered with Dash for the time being, replaced with a Welcome page.
"""
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
