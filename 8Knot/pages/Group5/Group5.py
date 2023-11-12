from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

from .visualizations.placeholder import gc_active_drifting_contributors
warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/Group5")


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_active_drifting_contributors, width=6),
                dbc.Col(gc_active_drifting_contributors, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        )
    ],
    fluid=True,
)