from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.gh_org_affiliation import gc_gh_org_affiliation
from .visualizations.unqiue_domains import gc_unique_domains
from .visualizations.org_associated_activity import gc_org_associated_activity
from .visualizations.org_core_contributors import gc_org_core_contributors
from .visualizations.commit_domains import gc_commit_domains

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/affiliation")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_unique_domains, width=6),
                dbc.Col(gc_commit_domains, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_org_associated_activity, width=6),
                dbc.Col(gc_org_core_contributors, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(gc_gh_org_affiliation, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
