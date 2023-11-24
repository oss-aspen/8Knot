from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.project_velocity import gc_project_velocity
from .visualizations.time_to_first_response import time_to_first_response
from .visualizations.bus_factor             import gc_bus_factor_pie

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/chaoss_1")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_bus_factor_pie, width=6),
                dbc.Col(time_to_first_response, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
