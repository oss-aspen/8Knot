from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.fork_count_graph import gc_fork_count_graph
from .visualizations.star_count_graph import gc_star_count_graph
from .visualizations.watchers_count_graph import gc_watchers_count_graph

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/starter-project-health")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_fork_count_graph, width=6),
                dbc.Col(gc_star_count_graph, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_watchers_count_graph, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
