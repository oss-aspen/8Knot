from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px
from pages.utils.graph_utils import color_seq
from queries.contributors_query import contributors_query as ctq
from cache_manager.cache_manager import CacheManager as cm
import io
import time
from pages.utils.job_utils import nodata_graph

gc_first_time_contributions = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    "First Time Contributions Per Quarter",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on graph 2"),
                    ],
                    id="chaoss-popover-2",
                    target="chaoss-popover-target-2",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id="first-time-contributions"),
                ),
                dbc.Row(
                    dbc.Button(
                        "About Graph",
                        id="chaoss-popover-target-2",
                        color="secondary",
                        size="small",
                    ),
                    style={"padding-top": ".5em"},
                ),
            ]
        ),
    ],
    color="light",
)


@callback(
    Output("chaoss-popover-2", "is_open"),
    [Input("chaoss-popover-target-2", "n_clicks")],
    [State("chaoss-popover-2", "is_open")],
)
def toggle_popover_2(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("first-time-contributions", "figure"),
    [
        Input("repo-choices", "data"),
    ],
    background=True,
)
def create_first_time_contributors_graph(repolist):

    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    start = time.perf_counter()
    logging.debug("CONTRIB_DRIVE_REPEAT_VIZ - START")

    # test if there is data
    if df.empty:
        logging.debug("1ST CONTRIBUTIONS - NO DATA AVAILABLE")
        return nodata_graph, False

    # function for all data pre processing
    df = process_data(df)

    fig = create_figure(df)

    logging.debug(f"1ST_CONTRIBUTIONS_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df):

    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df.rename(columns={"created_at": "created"}, inplace=True)

    # selection for 1st contribution only
    df = df[df["rank"] == 1]

    # reset index to be ready for plotly
    df = df.reset_index()

    return df


def create_figure(df):

    # Graph generation
    fig = px.histogram(df, x="created", color="Action", color_discrete_sequence=color_seq)
    fig.update_traces(
        xbins_size="M3",
        hovertemplate="Date: %{x}" + "<br>Amount: %{y}<br><extra></extra>",
    )
    fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M3")
    fig.update_layout(
        xaxis_title="Quarter",
        yaxis_title="Contributions",
        margin_b=40,
    )

    return fig
