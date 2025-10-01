from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import warnings

# import visualization cards
from .visualizations.contrib_activity_cycle import gc_contrib_activity_cycle
from .visualizations.contribs_by_action import gc_contribs_by_action
from .visualizations.contrib_importance_pie import gc_contrib_importance_pie
from .visualizations.contrib_importance_over_time import gc_lottery_factor_over_time

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/contributors/contribution_types")

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(gc_contribs_by_action, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_contrib_activity_cycle, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_contrib_importance_pie, xl=10),
            className="visualization-row",
        ),
        dbc.Row(
            dbc.Col(gc_lottery_factor_over_time, xl=10),
            className="visualization-row",
        ),
    ],
    fluid=True,
)
