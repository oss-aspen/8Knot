from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.bus_factor import gc_bus_factor
from .visualizations.cr_closure import gc_cr_closure
from .visualizations.first_response import gc_first_response
from .visualizations.release_freq import gc_release_freq

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/starterHealth")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_bus_factor, width=6),
                dbc.Col(gc_cr_closure, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_first_response, width=6),
                dbc.Col(gc_release_freq, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
