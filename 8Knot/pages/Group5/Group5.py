from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

from .visualizations.time_to_first_response import time_to_first_response
from .visualizations.change_request_closure_ratio import change_request_closure_ratio
from .visualizations.bus_factor import bus_factor
from .visualizations.release_frequency import release_frequency

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/Group5")


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(time_to_first_response, width=6),
                dbc.Col(change_request_closure_ratio, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(bus_factor, width=6),
                dbc.Col(release_frequency, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        )
    ],
    fluid=True,
)