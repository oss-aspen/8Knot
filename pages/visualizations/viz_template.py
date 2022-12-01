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
from queries.QUERRY_USED import QUERRY_NAME as QUERRY_INITIALS
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time

# TODO: REMOVE UNUSED IMPORTS

page = "overview"  # EDIT FOR PAGE USED
viz_id = "shortname-of-viz"  # UNIQUE IDENTIFIER FOR CALLBAKCS, MUST BE UNIQUE

"""
USE IN CASE OF ADDITIONAL PARAMETERS
paramter_1 = "name-of-additional-graph-input"
paramter_2 = "name-of-additional-graph-input
"""

gc_VISUALIZATION_NAME_HERE = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    "TITLE OF VISUALIZATION",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("INSERT CONTEXT OF GRAPH HERE"),
                    ],
                    id=f"{page}-popover-{viz_id}",
                    target=f"{page}-popover-target-{viz_id}",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=viz_id),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"{viz_id}-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"{viz_id}-interval",
                                            options=[
                                                {"label": "Trend", "value": "D"},  # TREND IF LINE, DAY IF NOT
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
                                        id=f"{page}-popover-target-{viz_id}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
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
                                    style={"font-weight": "bold"},
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
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=paramter_2,
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=30,
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Alert(
                            children="Please ensure that 'PARAMETER' is less than 'PARAMETER'",
                            id= viz_id + "-check-alert",
                            dismissable=True,
                            fade=False,
                            is_open=False,
                            color="warning",
                        ),""",
                    ]
                ),
            ]
        )
    ],
    color="light",
)

# call backs for card graph NUMER - VIZ TITLE
@callback(
    Output(f"{page}-popover-{viz_id}", "is_open"),
    [Input(f"{page}-popover-target-{viz_id}", "n_clicks")],
    [State(f"{page}-popover-{viz_id}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for VIZ TITLE graph
@callback(
    Output(viz_id, "figure"),
    # Output(viz_id + "-check-alert", "is_open"), USE WITH ADDITIONAL PARAMETERS
    # if additional output is added, change returns accordingly
    [
        Input("repo-choices", "data"),
        Input(viz_id + "-interval", "value"),
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
    df = cache.grabm(func=QUERRY_INITIALS, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=QUERRY_INITIALS, repos=repolist)

    start = time.perf_counter()
    logging.debug("NAME OF GRAPH - START")

    # test if there is data
    if df.empty:
        logging.debug("NAME OF GRAPH - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.debug(f"NAME OF GRAPH - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):

    # convert to datetime objects rather than strings
    # ADD ANY OTHER COLUMNS WITH DATETIME
    df["COLUMN_WITH_DATETIME"] = pd.to_datetime(df["COLUMN_WITH_DATETIME"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="COLUMN_TO_SORT_BY", axis=0, ascending=True)

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR DATA PROCESS"""

    return df


def create_figure(df_status: pd.DataFrame, interval):

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    fig = fig

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR GRAPH"""

    return fig
