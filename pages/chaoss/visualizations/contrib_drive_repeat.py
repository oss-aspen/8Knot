from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px
from pages.utils.graph_utils import color_seq
from pages.utils.job_utils import nodata_graph
from queries.contributors_query import contributors_query as ctq
import time
import io
from cache_manager.cache_manager import CacheManager as cm

gc_contrib_drive_repeat = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    id="chaoss-graph-title-1",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This graph gives a break down of how many and what type of contributions\n\
                            different types of contributors in your community make. By your community standard you can\n\
                            have the critera of how many contributions it takes for a member to be a repeat contributor."
                        ),
                    ],
                    id="chaoss-popover-1",
                    target="chaoss-popover-target-1",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id="cont-drive-repeat"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Contributions Required:",
                                    html_for="num_contributions",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="num_contributions",
                                        type="number",
                                        min=1,
                                        max=15,
                                        step=1,
                                        value=4,
                                        size="sm",
                                    ),
                                    className="me-2",
                                    width=1,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Graph View:",
                                    html_for="drive-repeat",
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="drive-repeat",
                                        options=[
                                            {
                                                "label": "Repeat",
                                                "value": "repeat",
                                            },
                                            {
                                                "label": "Drive-By",
                                                "value": "drive",
                                            },
                                        ],
                                        value="drive",
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="chaoss-popover-target-1",
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
        ),
    ],
    # color="light",
)

# callback for graph info popover
@callback(
    Output("chaoss-popover-1", "is_open"),
    [Input("chaoss-popover-target-1", "n_clicks")],
    [State("chaoss-popover-1", "is_open")],
)
def toggle_popover_1(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for dynamically changing the graph title
@callback(Output("chaoss-graph-title-1", "children"), Input("drive-repeat", "value"))
def graph_title(view):
    title = ""
    if view == "drive":
        title = "Drive-by Contributions Per Quarter"
    else:
        title = "Repeat Contributions Per Quarter"
    return title


# call back for drive by vs commits over time graph
@callback(
    Output("cont-drive-repeat", "figure"),
    [
        Input("repo-choices", "data"),
        Input("num_contributions", "value"),
        Input("drive-repeat", "value"),
    ],
    background=True,
)
def repeat_drive_by_graph(repolist, contribs, view):

    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    # data ready.
    start = time.perf_counter()
    logging.debug("CONTRIB_DRIVE_REPEAT_VIZ - START")

    # test if there is data
    if df.empty:
        logging.debug("CONTRIB DRIVE REPEAT - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df_cont_subset = process_data(df, view, contribs)

    # test if there is data
    if df_cont_subset.empty:
        logging.debug("CONTRIB DRIVE REPEAT - NO DRIVE OR REPEAT DATA")
        return nodata_graph

    fig = create_figure(df_cont_subset)

    logging.debug(f"CONTRIB_DRIVE_REPEAT_VIZ - END - {time.perf_counter() - start}")

    return fig


def process_data(df, view, contribs):

    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df.rename(columns={"created_at": "created"}, inplace=True)

    # graph on contribution subset
    contributors = df["cntrb_id"][df["rank"] == contribs].to_list()
    df_cont_subset = pd.DataFrame(df)

    # filtering data by view
    if view == "drive":
        df_cont_subset = df_cont_subset.loc[
            ~df_cont_subset["cntrb_id"].isin(contributors)
        ]
    else:
        df_cont_subset = df_cont_subset.loc[
            df_cont_subset["cntrb_id"].isin(contributors)
        ]

    # reset index to be ready for plotly
    df_cont_subset = df_cont_subset.reset_index()

    return df_cont_subset


def create_figure(df_cont_subset):
    # create plotly express histogram
    fig = px.histogram(
        df_cont_subset, x="created", color="Action", color_discrete_sequence=color_seq
    )

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
