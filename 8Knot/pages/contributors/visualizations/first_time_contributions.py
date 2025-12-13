from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import polars as pl
import logging
import plotly.express as px
from pages.utils.graph_utils import baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from queries.contributors_query import contributors_query as ctq
import time
from pages.utils.job_utils import nodata_graph
import app
import pages.utils.preprocessing_utils as preproc_utils
import cache_manager.cache_facade as cf

PAGE = "contributors"
VIZ_ID = "first-time-contribution"

gc_first_time_contributions = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "First Time Contributors Per Quarter",
                                className="card-title",
                                style={"textAlign": "center"},
                            ),
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                color="outline-secondary",
                                size="sm",
                                className="about-graph-button",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    justify="between",
                    className="mb-3",
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
            ]
        ),
    ],
    className="dark-card",
    id="first-time-contributors",
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
        Input("bot-switch", "value"),
    ],
    background=True,
)
def create_first_time_contributors_graph(repolist, bot_switch):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=ctq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=ctq.__name__,
        repolist=repolist,
    )

    df = preproc_utils.contributors_df_action_naming(df)

    # test if there is data
    if df.empty:
        logging.warning("1ST CONTRIBUTIONS - NO DATA AVAILABLE")
        return nodata_graph

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # function for all data pre processing
    df = process_data(df)

    fig = create_figure(df)

    logging.warning(f"1ST_CONTRIBUTIONS_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df):
    """
    Process first-time contribution data using Polars for performance.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast processing
    pl_df = to_polars(df)

    # Convert to datetime
    pl_df = pl_df.with_columns(pl.col("created_at").cast(pl.Datetime("us", "UTC")))

    # Filter for first contributions only (rank == 1)
    pl_df = pl_df.filter(pl.col("rank") == 1)

    # === POLARS PROCESSING END ===

    # Convert to Pandas for visualization
    return to_pandas(pl_df)


def create_figure(df):
    # create plotly express histogram
    fig = px.histogram(df, x="created_at", color="Action", color_discrete_sequence=baby_blue)

    # creates bins with 3 month size and customizes the hover value for the bars
    fig.update_traces(
        xbins_size="M3",
        hovertemplate="Date: %{x}" + "<br>Amount: %{y}",
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
