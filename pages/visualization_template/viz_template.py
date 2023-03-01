from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.QUERY_USED import QUERY_NAME as QUERY_INITIALS
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time

"""
List of variables to change:
(1) PAGE
(2) VIZ_ID
(3) TITLE OF VISUALIZATION
(4) CONTEXT OF GRAPH
(5) TITLE OF VISUALIZATION
(6) COLUMN_WITH_DATETIME
(7) COLUMN_WITH_DATETIME
(8) COLUMN_TO_SORT_BY
(9) Comments before callbacks
(10) QUERY_USED, QUERY_NAME, QUERY_INITIALS

NOTE: If you add addtional graph inputs, the one on the same row as the graph info button (date) should be last
"""


# TODO: Remove unused imports and edit strings and variables in all CAPS

PAGE = "overview"  # EDIT FOR PAGE USED
VIZ_ID = "shortname-of-viz"  # UNIQUE IDENTIFIER FOR CALLBAKCS, MUST BE UNIQUE

"""
ADDITIONAL INPUT/OUTPUT PARAMETER NAMES FOR DASH CALLBACKS
If you add a new Input() or Output() to your visualization, name them here

paramter_1 = "name-of-additional-graph-input"
paramter_2 = "name-of-additional-graph-input
"""

gc_VISUALIZATION_NAME_HERE = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "TITLE OF VISUALIZATION",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("INSERT CONTEXT OF GRAPH HERE"),
                    ],
                    id=f"{PAGE}-popover-{VIZ_ID}",
                    target=f"{PAGE}-popover-target-{VIZ_ID}",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=VIZ_ID),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"{VIZ_ID}-interval",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"{VIZ_ID}-interval",
                                            options=[
                                                {
                                                    "label": "Trend",
                                                    "value": "D",
                                                },  # TREND IF LINE, DAY IF NOT
                                                # {"label": "Week","value": "W",}, UNCOMMENT IF APPLICABLE
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
                                            inline=True,
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"{PAGE}-popover-target-{VIZ_ID}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                        # TODO: ADD IN IF ADDITIONAL PARAMETERS FOR GRAPH, REMOVE IF NOT
                        """dbc.Row(
                            [
                                dbc.Label(
                                    "TITLE_OF_ADDITIONAL_PARAMETER:",
                                    html_for=paramter_1,
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=paramter_1,
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=7,
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "TITLE_OF_ADDITIONAL_PARAMETER:",
                                    html_for=paramter_2,
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=paramter_2,
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=30,
                                        size= "sm"
                                    ),
                                    className="me-2",
                                    width=1,
                                ),
                                dbc.Alert(
                                    children="Please ensure that 'PARAMETER' is less than 'PARAMETER'",
                                    id= VIZ_ID + "-check-alert",
                                    dismissable=True,
                                    fade=False,
                                    is_open=False,
                                    color="warning",
                                ),
                            ],
                            align="center",
                        ),
                        """,
                    ]
                ),
            ]
        )
    ],
)

# callback for graph info popover
@callback(
    Output(f"{PAGE}-popover-{VIZ_ID}", "is_open"),
    [Input(f"{PAGE}-popover-target-{VIZ_ID}", "n_clicks")],
    [State(f"{PAGE}-popover-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for VIZ TITLE graph
@callback(
    Output(VIZ_ID, "figure"),
    # Output(VIZ_ID + "-check-alert", "is_open"), USE WITH ADDITIONAL PARAMETERS
    # if additional output is added, change returns accordingly
    [
        Input("repo-choices", "data"),
        Input(VIZ_ID + "-interval", "value"),
        """
        USE IN CASE OF ADDITIONAL PARAMETERS, MUST REMOVE IF NOT
        Input(paramter_1, "value"),
        Input(paramter_2, "value"),
        """,
    ],
    background=True,
)
def NAME_OF_VISUALIZATION_graph(repolist, interval):

    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=QUERY_INITIALS, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=QUERY_INITIALS, repos=repolist)

    start = time.perf_counter()
    logging.debug(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.debug(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.debug(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""

    # convert to datetime objects rather than strings
    # ADD ANY OTHER COLUMNS WITH DATETIME
    df["COLUMN_WITH_DATETIME"] = pd.to_datetime(df["COLUMN_WITH_DATETIME"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="COLUMN_TO_SORT_BY", axis=0, ascending=True)

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR DATA PROCESS"""

    return df


def create_figure(df: pd.DataFrame, interval):

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    fig = fig

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR GRAPH"""

    return fig
