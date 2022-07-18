from dash import html, dcc
import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.chaoss.contrib_drive_repeat import gc_contrib_drive_repeat
from .visualizations.chaoss.first_time_contributions import gc_first_time_contributions
from .visualizations.chaoss.contributors_over_time import gc_contributors_over_time

warnings.filterwarnings("ignore")

# register the page
dash.register_page(__name__, order=3)


layout = dbc.Container(
    [
        dbc.Row([dbc.Col([html.H1(children="Chaoss Page - WIP")])]),
        dbc.Row(
            [
                dbc.Col(gc_contrib_drive_repeat, width=6),
                dbc.Col(gc_first_time_contributions, width=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(gc_contributors_over_time, width=6),
            ]
        ),
    ],
    fluid=True,
)
