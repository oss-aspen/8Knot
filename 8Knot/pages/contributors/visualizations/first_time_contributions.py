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
                                "First Time Contributions Per Quarter",
                                className="card-title",
                                style={"textAlign": "left", "fontSize": "20px", "color": "white"},
                            ),
                            width=10,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                className="text-white font-medium rounded-lg px-3 py-1.5 transition-all duration-200 cursor-pointer text-sm custom-hover-button",
                                style={
                                    "backgroundColor": "#292929",
                                    "borderColor": "#404040",
                                    "color": "white",
                                    "borderRadius": "20px",
                                    "padding": "6px 12px",
                                    "fontSize": "14px",
                                    "fontWeight": "500",
                                    "border": "1px solid #404040",
                                    "cursor": "pointer",
                                    "transition": "all 0.2s ease",
                                    "backgroundImage": "none",
                                    "boxShadow": "none",
                                },
                            ),
                            width=2,
                            className="d-flex justify-content-end",
                        ),
                    ],
                    align="center",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader(
                            "Graph Info:",
                            style={
                                "backgroundColor": "#404040",
                                "color": "white",
                                "border": "none",
                                "borderBottom": "1px solid #606060",
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "padding": "12px 16px",
                            },
                        ),
                        dbc.PopoverBody(
                            """
                            Visualizes the arrival of net-new contributors to a project\n
                            and differentiates them by their first in-project action.
                            """,
                            style={
                                "backgroundColor": "#292929",
                                "color": "#E0E0E0",
                                "border": "none",
                                "fontSize": "14px",
                                "lineHeight": "1.5",
                                "padding": "16px",
                            },
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                    style={
                        "backgroundColor": "#292929",
                        "border": "1px solid #606060",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.3)",
                        "maxWidth": "400px",
                    },
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                html.Hr(
                    style={
                        "borderColor": "#e0e0e0",
                        "margin": "1.5rem -2rem",
                        "width": "calc(100% + 4rem)",
                        "marginLeft": "-2rem",
                    }
                ),
            ]
        ),
    ],
    style={"padding": "20px", "borderRadius": "10px", "backgroundColor": "#292929", "border": "1px solid #404040"},
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
    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    # df.rename(columns={"created_at": "created"}, inplace=True)

    # selection for 1st contribution only
    df = df[df["rank"] == 1]

    # reset index to be ready for plotly
    df = df.reset_index()

    return df


def create_figure(df):
    # create plotly express histogram
    fig = px.histogram(df, x="created_at", color="Action", color_discrete_sequence=color_seq)

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
        plot_bgcolor="#292929",
        paper_bgcolor="#292929",
    )

    return fig
