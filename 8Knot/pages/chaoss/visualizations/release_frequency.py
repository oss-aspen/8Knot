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
from queries.releases_query import RELEASES_query as rq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

"""
NOTE: VARIABLES TO CHANGE:

(1) PAGE
(2) VIZ_ID
(3) gc_VISUALIZATION
(4) TITLE OF VISUALIZATION
(5) CONTEXT OF GRAPH
(6) IDs of Dash components
(6) NAME_OF_VISUALIZATION_graph
(7) COLUMN_WITH_DATETIME
(8) COLUMN_WITH_DATETIME
(9) COLUMN_TO_SORT_BY
(10) Comments before callbacks
(11) QUERY_USED, QUERY_NAME, QUERY_INITIALS

NOTE: IMPORTING A VISUALIZATION INTO A PAGE
(1) Include the visualization file in the visualization folder for the respective page
(2) Import the visualization into the page_name.py file using "from .visualizations.visualization_file_name import gc_visualization_name"
(3) Add the card into a column in a row on the page

NOTE: ADDITIONAL DASH COMPONENTS FOR USER GRAPH CUSTOMIZATIONS

If you add Dash components (ie dbc.Input, dbc.RadioItems, dcc.DatePickerRange...) the ids, html_for, and targets should be in the
following format: f"component-identifier-{PAGE}-{VIZ_ID}"

NOTE: If you change or add a new query, you need to do "docker system prune -af" before building again

NOTE: If you use an alert or take code from a visualization that uses one, make sure to update returns accordingly in the NAME_OF_VISUALIZATION_graph

For more information, check out the new_vis_guidance.md
"""


# TODO: Remove unused imports and edit strings and variables in all CAPS
# TODO: Remove comments specific for the template

PAGE = "chaoss"  # EDIT FOR CURRENT PAGE
VIZ_ID = "release-freq-viz"  # UNIQUE IDENTIFIER FOR VIZUALIZATION

gc_RELEASE_FREQUENCY = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "RELEASE FREQUENCY",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("INSERT CONTEXT OF GRAPH HERE"),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-radio-{PAGE}-{VIZ_ID}",
                                            options=[

                                                {"label": "Week","value": "W",},
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
                                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                        # # TODO: ADD IN IF ADDITIONAL PARAMETERS FOR GRAPH, REMOVE IF NOT
                        # """ format dbc.Inputs, including dbc.Alert if needed
                        #         dbc.Label(
                        #             "TITLE_OF_ADDITIONAL_PARAMETER:",
                        #             html_for=f"component-identifier-{PAGE}-{VIZ_ID}",
                        #             width={"size": "auto"},
                        #         ),
                        #         dbc.Col(
                        #             dbc.Input(
                        #                 id=f"component-identifier-{PAGE}-{VIZ_ID}",,
                        #                 type="number",
                        #                 min=1,
                        #                 max=120,
                        #                 step=1,
                        #                 value=7,
                        #             ),
                        #             className="me-2",
                        #             width=2,
                        #         ),
                        #         dbc.Alert(
                        #             children="Please ensure that 'PARAMETER' is less than 'PARAMETER'",
                        #             id=f"component-identifier-{PAGE}-{VIZ_ID}",
                        #             dismissable=True,
                        #             fade=False,
                        #             is_open=False,
                        #             color="warning",
                        #         ),
                        # """
                        # """ format for dcc.DatePickerRange:
                        # dbc.Col(
                        #     dcc.DatePickerRange(
                        #         id=f"date-range-{PAGE}-{VIZ_ID}",
                        #         min_date_allowed=dt.date(2005, 1, 1),
                        #         max_date_allowed=dt.date.today(),
                        #         clearable=True,
                        #     ),
                        #     width="auto",
                        # ),

                        # """,
                    ]
                ),
            ]
        )
    ],
)


# callback for graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for VIZ TITLE graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    # Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"), USE WITH ADDITIONAL PARAMETERS
    # if additional output is added, change returns accordingly
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "interval"),
        # Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        # Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
        # add additional inputs here
    ],
    background=True,
)
def RELEASE_FREQUENCY_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=rq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=rq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")
    logging.warning(df)
    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""
    x_r, x_name, hover, period = get_graph_time_values(interval)
    # convert to datetime objects rather than strings
    # ADD ANY OTHER COLUMNS WITH DATETIME
    df["release_published_at"] = pd.to_datetime(df["release_published_at"], utc=True)

    # filter values based on date picker
    df = df[pd.to_datetime(df.release_published_at).dt.date >= (dt.date.today() - dt.timedelta(days=365))]

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR DATA PROCESS"""

    return df


def create_figure(df: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    fig = px.scatter(
        df,
        x="release_published_at",
        y="repo_name",
        color="repo_name",
        size="id",
        size_max=15,
        hover_data=["repo_name", "release_name", "release_published_at"],
        color_discrete_sequence=color_seq
    )

    fig.update_traces(
        hovertemplate="Repo: %{customdata[0]} <br>Release Name: %{customdata[1]} <br>Relase Published: %{customdata[2]}"
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Repo",
        margin_b=40,
        font=dict(size=14),
        legend_title="Repo Name",
    )

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR GRAPH"""

    return fig
