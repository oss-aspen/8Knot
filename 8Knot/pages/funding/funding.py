from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.contr_attr import gc_contr_attr
from .visualizations.contr_type import gc_contr_type
from .visualizations.org_inf import gc_org_inf
from .visualizations.org_div import gc_org_div
from .visualizations.labor_inv import gc_labor_inv

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/funding")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_contr_attr, width=6),
                dbc.Col(gc_contr_type, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_org_div, width=6),
                dbc.Col(gc_org_inf, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_labor_inv, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
