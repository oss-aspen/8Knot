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
from queries.ttfr_query import TTFRQ_query as ttfrq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time

"""
NOTE: VARIABLES TO CHANGE:
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

PAGE = "Group5"  # EDIT FOR CURRENT PAGE
VIZ_ID = "time_to_first_response"  # UNIQUE IDENTIFIER FOR VIZUALIZATION

time_to_first_response = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Time To First Response",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Graph of time time between commit and response"),
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
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        # add additional inputs here
    ],
    background=True,
)
def time_to_first_response_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ttfrq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ttfrq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df, df_contribs = process_data(df, interval)

    fig = create_figure(df, df_contribs, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df["closed_at"] = pd.to_datetime(df["closed_at"], utc=True)

    created_range = pd.to_datetime(df["created"]).dt.to_period(interval).value_counts().sort_index()

    # converts to data frame object and creates date column from period values
    df_contribs = created_range.to_frame().reset_index().rename(columns={"index": "Date", "created": "contribs"})

    # converts date column to a datetime object, converts to string first to handle period information

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #NEED TO SUBTRACT END DATE BY START DATE AND MAKE THAT THE Y AXIS VALUE+
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    df_contribs["created_at"] = pd.to_numeric(df_contribs["created_at"])
    df_contribs["closed_at"] = pd.to_datetime(df_contribs["closed_at"].astype(str))

    # correction for year binning -
    # rounded up to next year so this is a simple patch
    if interval == "Y":
        df_contribs["Date"] = df_contribs["Date"].dt.year
    elif interval == "M":
        df_contribs["Date"] = df_contribs["Date"].dt.strftime("%Y-%m")

    return df, df_contribs


def create_figure(df: pd.DataFrame, df_contribs, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    if interval == -1:
        fig = px.line(df, x="created_at", y=df.index, color_discrete_sequence=[color_seq[3]])
        # fig.update_traces(hovertemplate="Contributors: %{y}<br>%{x|%b %d, %Y} <extra></extra>")
    else:
        fig = px.bar(
            df_contribs,
            x="Date",
            y="Time to Respond",
            range_x=x_r,
            labels={"x": x_name, "y": "Contributors"},
            color_discrete_sequence=[color_seq[3]],
        )
        fig.update_traces(hovertemplate=hover + "<br>Contributors: %{y}<br>")

    """
        Ref. for this awesome button thing:
        https://plotly.com/python/range-slider/
    """
    # add the date-range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )
    # label the figure correctly
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Contributors",
        margin_b=40,
        margin_r=20,
        font=dict(size=14),
    )
    return fig