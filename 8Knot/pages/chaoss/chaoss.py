from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.project_velocity import gc_project_velocity
from .visualizations.contrib_importance_pie import gc_contrib_importance_pie

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/chaoss")

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                dbc.Alert(
                    [
                        "New to open source metrics? The ",
                        html.A(
                            "CHAOSS Practitioner Guide",
                            href="https://chaoss.community/practitioner-guide-introduction/",
                            target="_blank",
                            rel="noopener noreferrer",
                            className="alert-link",
                        ),
                        " explains how to interpret community health charts.",
                    ],
                    color="info",
                    className="mb-3",
                ),
                xl=10,
            ),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_contrib_importance_pie, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_project_velocity, xl=10),
            className="visualization-row",
        ),
    ],
    fluid=True,
)
