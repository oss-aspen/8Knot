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

PAGE = "chaoss"
VIZ_ID = "first-time-contribution"

gc_first_time_contributions = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "First Time Contributions Per Quarter",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes the arrival of net-new contributors to a project\n
                            and differentiates them by their first in-project action.
                            """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Row(
                    dbc.Button(
                        "About Graph",
                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                        color="secondary",
                        size="small",
                    ),
                    style={"paddingTop": ".5em"},
                ),
            ]
        ),
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


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
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
    logging.warning("CONTRIB_DRIVE_REPEAT_VIZ - START")

    # test if there is data
    if df.empty:
        logging.warning("1ST CONTRIBUTIONS - NO DATA AVAILABLE")
        return nodata_graph, False

    # function for all data pre processing
    df = process_data(df)

    fig = create_figure(df)

    logging.warning(f"1ST_CONTRIBUTIONS_VIZ - END - {time.perf_counter() - start}")
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
    # create plotly express histogram
    fig = px.histogram(df, x="created", color="Action", color_discrete_sequence=color_seq)

    # creates bins with 3 month size and customizes the hover value for the bars
    fig.update_traces(
        xbins_size="M3",
        hovertemplate="Date: %{x}" + "<br>Amount: %{y}<br><extra></extra>",
    )

    # update xaxes to align for the 3 month bin size
    fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M3")

    # layout styling
    fig.update_layout(
        xaxis_title="Quarter",
        yaxis_title="Contributions",
        margin_b=40,
        font=dict(size=14),
    )

    return fig
