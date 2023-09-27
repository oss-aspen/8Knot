from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.contrib_drive_repeat import gc_contrib_drive_repeat
from .visualizations.first_time_contributions import gc_first_time_contributions
from .visualizations.contributors_types_over_time import gc_contributors_over_time
from .visualizations.active_drifting_contributors import gc_active_drifting_contributors
from .visualizations.new_contributor import gc_new_contributor

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/contributors/behavior")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_contrib_drive_repeat, width=6),
                dbc.Col(gc_first_time_contributions, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_active_drifting_contributors, width=6),
                dbc.Col(gc_new_contributor, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_contributors_over_time, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
