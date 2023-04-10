from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.gh_company_affiliation import gc_gh_company_affiliation
from .visualizations.unqiue_domains import gc_unique_domains

warnings.filterwarnings("ignore")

# register the page
dash.register_page(__name__, path="/company", order=4)


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_gh_company_affiliation, width=6),
                dbc.Col(gc_unique_domains, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
