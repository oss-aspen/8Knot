from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.change_request_review_duration import gc_change_request_review_duration

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/communityservicesupport")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_change_request_review_duration, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
