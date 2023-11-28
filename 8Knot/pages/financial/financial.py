from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
#from .visualizations.project_velocity import gc_project_velocity
#from .visualizations.contrib_importance_pie import gc_contrib_importance_pie
from .visualizations.test_graph import gc_test_graph

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/financial")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_test_graph, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
