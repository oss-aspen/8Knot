from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.contrib_drive_repeat import gc_contrib_drive_repeat
from .visualizations.contributors_types_over_time import gc_contributors_over_time
from .visualizations.project_velocity import gc_project_velocity
from .visualizations.contrib_importance_pie import gc_contrib_importance_pie

warnings.filterwarnings("ignore")

# register the page
dash.register_page(__name__, path="/chaoss", order=5)


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_contrib_importance_pie, width=6),
                dbc.Col(gc_project_velocity, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_contrib_drive_repeat, width=6),
                dbc.Col(gc_contributors_over_time, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
