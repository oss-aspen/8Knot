from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.contrib_drive_repeat import gc_contrib_drive_repeat
from .visualizations.first_time_contributions import gc_first_time_contributions
from .visualizations.contributors_over_time import gc_contributors_over_time
from .visualizations.contrib_activity_cycle import gc_contrib_activity_cycle

warnings.filterwarnings("ignore")

# register the page
dash.register_page(__name__, path="/chaoss", order=3)


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
                dbc.Col(gc_contributors_over_time, width=6),
                dbc.Col(gc_contrib_activity_cycle, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
