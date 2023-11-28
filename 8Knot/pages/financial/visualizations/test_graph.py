from dash import html, dcc, callback
import dash
from dash import dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.contributors_query import contributors_query as ctq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

PAGE = "financial"
VIZ_ID = "test-graph"

gc_test_graph = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    id="Test Graph",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("This is a test"),
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
                        )
                    ]
                )
            ]
        )
    ]
)

@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def create_test_graph(repolist, interval):
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False
    
    df = process_data(df, interval)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig
    


def process_data(df: pd.DataFrame, interval):
    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # order values chronologically by created_at date
    df = df.sort_values(by="created_at", ascending=True)

    # filter values based on date picker
    if interval is not None:
        df = df[df.created_at >= interval]

    # count the number of contributions for each contributor
    df = (df.groupby("cntrb_id")["Action"].count()).to_frame()

    # sort rows according to amount of contributions from greatest to least
    df.sort_values(by="cntrb_id", ascending=False, inplace=True)
    df = df.reset_index()

    # convert cntrb_id from type UUID to String
    df["cntrb_id"] = df["cntrb_id"].apply(lambda x: str(x).split("-")[0])

    return df


def create_figure(df: pd.DataFrame):
    # create plotly express pie chart
    fig = px.pie(
        df,
        names="cntrb_id",  # can be replaced with login to unanonymize
        values="test stuff",
        color_discrete_sequence=color_seq,
    )

    # display percent contributions and cntrb_id in each wedge
    # format hover template to display cntrb_id and the number of their contributions according to the action_type
    fig.update_traces(
        textinfo="percent+label",
        textposition="inside",
        hovertemplate="Contributor ID: %{label} <br>Contributions: %{value}<br><extra></extra>",
    )

    # add legend title
    fig.update_layout(legend_title_text="Contributor ID")

    return fig