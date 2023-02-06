from dash import html
import dash
import dash_bootstrap_components as dbc
from .visualizations.commit_metrics import gc_commit_metrics
from .visualizations.pr_metrics import gc_pr_metrics
from .visualizations.issue_metrics import gc_issue_metrics

# register the page
dash.register_page(__name__, path="/", order=1)

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
                dbc.Col(
                    [
                        html.H4(
                            "App Notes",
                            # className="font-weight-bold mb-4",
                        ),
                        html.P(
                            "Plotly graphs have a mode bar if you hover over the top of the title.",
                            className="font-weight-bold mb-4",
                        ),
                        html.P(
                            "If you want to reset the view of a graph with customization options, toggle one of the options to reset the view.",
                            className="font-weight-bold mb-4",
                        ),
                    ]
                )
            ]
        ),
    ],
    fluid=True,
)
