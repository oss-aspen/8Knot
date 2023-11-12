from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.bus_factor import gc_bus_factor
from .visualizations.contribution_attribution import gc_contribution_attribution
from .visualizations.labor_investment import gc_labor_investment
from .visualizations.organizational_diversity import gc_Organizational_diversity
from .visualizations.organizational_influence import gc_organizational_influence
from .visualizations.release_frequency import gc_release_frequency
from .visualizations.time_to_first_response import gc_time_to_first_response
from .visualizations.types_of_contributions import gc_types_of_contributions
from .visualizations.change_request_closure_ratio import gc_change_request_closure_ratio

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/new_tab")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(gc_bus_factor, width=6),
                dbc.Col(gc_contribution_attribution, width=6),
                dbc.Col(gc_labor_investment, width=6),
                dbc.Col(gc_Organizational_diversity, width=6),
                dbc.Col(gc_organizational_influence, width=6),
                dbc.Col(gc_release_frequency, width=6),
                dbc.Col(gc_time_to_first_response, width=6),
                dbc.Col(gc_types_of_contributions, width=6),
                dbc.Col(gc_change_request_closure_ratio, width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
