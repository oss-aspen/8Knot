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
from queries.commits_query import commits_query as ctq
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

PAGE = "chaoss"
VIZ_ID = "bus-factor-viz"

gc_bus_factor = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Bus Factor",
                    id=f"Bus Factor",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("A graph that calculates the bus factor of a given repo by showing a contributors value through their contributions. This is a decent indicator of the overall health and consistency of a project."),
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
                        # dbc.Row(
                            # [
                                # dbc.Label(
                                #     "Date Interval:",
                                #     html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                #     width="auto",
                                # ),
                                # dbc.Col(
                                #     [
                                #         dbc.RadioItems(
                                #             id=f"date-radio-{PAGE}-{VIZ_ID}",
                                #             options=[

                                #                 {"label": "Week","value": "W",},
                                #                 {"label": "Month", "value": "M"},
                                #                 {"label": "Year", "value": "Y"},
                                #             ],
                                #             value="M",
                                #             inline=True,
                                #         ),
                                #     ]
                                # ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dcc.DatePickerRange(
                                            id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                            min_date_allowed=dt.date(2005, 1, 1),
                                            max_date_allowed=dt.date.today(),
                                            initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                            clearable=True,
                                        ),
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "About Graph",
                                            id=f"popover-target-{PAGE}-{VIZ_ID}",
                                            color="secondary",
                                            size="sm",
                                        ),
                                    ],
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                        # TODO: ADD IN IF ADDITIONAL PARAMETERS FOR GRAPH, REMOVE IF NOT
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

# callback for date range changed
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)

def bus_factor_graph(repolist, start_date, end_date):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")
    logging.warning(df)
    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    # Used to calculate bus factor
    df = process_data(df, start_date, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, start_date, end_date):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""
    # Convert 'date' column to datetime and sort by date. 
    # Filter by start_date and end_date.
    df = (
        df.assign(date=pd.to_datetime(df['date'], utc=True))
        .sort_values(by='date')
        .pipe(lambda x: x[x.date >= start_date] if start_date is not None else x)
        .pipe(lambda x: x[x.date <= end_date] if end_date is not None else x)
        .assign(month=lambda x: x['date'].dt.to_period('M'))
    )

    # Create a pivot table to aggregate data by 'month' and 'author_email'
    # Count occurrences for each combination of 'month' and 'author_email'
    result_df = (
        df.pivot_table(index=['month', 'author_email'], aggfunc='size', fill_value=0)
        .reset_index(name='commits')
    )

    # Calculate bus factor
    # Number of contributors per month responsible for 50% of commits
    def calculate_bus(group):
        sorted_group = group.sort_values(by='commits', ascending=False)
        sorted_group['total_sum'] = sorted_group['commits'].cumsum()
        index_half = sorted_group['total_sum'].searchsorted(sorted_group['commits'].sum() * 0.5)
        return pd.Series({'authors_num': index_half + 1})

    # Group by 'month' and apply the function to calculate the bus factor
    authors_df = result_df.groupby('month').apply(calculate_bus).reset_index()
    authors_df['month'] = authors_df['month'].astype(str)

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR DATA PROCESS"""

    return authors_df

def create_figure(df: pd.DataFrame):
    # Graph generation
    fig = px.bar(
        df,
        x="month",
        y="authors_num",
        color="authors_num",
        color_continuous_scale="Viridis"
    )

    # Layout customization
    fig.update_layout(
        title="Bus Factor by Month",
        xaxis_title="Month",
        yaxis_title="Number of Authors for Half of Commits",
        legend_title="Number of Authors",
        coloraxis_colorbar=dict(title="Number of Authors")
    )

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR GRAPH"""

    return fig