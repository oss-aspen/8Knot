from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px

from pages.utils.job_utils import nodata_graph
from queries.contributors_query import contributors_query as ctq
import time
import io
from cache_manager.cache_manager import CacheManager as cm

gc_contrib_drive_repeat = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    id="chaoss-graph-title-1",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on graph 1"),
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
                                    "Graph View:",
                                    html_for="drive-repeat",
                                    width="auto",
                                    style={"font-weight": "bold"},
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
                                    style={"padding-top": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Contributions Required:",
                                    html_for="num_contributions",
                                    width={"size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="num_contributions",
                                        type="number",
                                        min=1,
                                        max=15,
                                        step=1,
                                        value=4,
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
    color="light",
)


@callback(
    Output("chaoss-popover-1", "is_open"),
    [Input("chaoss-popover-target-1", "n_clicks")],
    [State("chaoss-popover-1", "is_open")],
)
def toggle_popover_1(n, is_open):
    if n:
        return not is_open
    return is_open


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
def create_drive_by_graph(repolist, contribs, view):

    num_repos = len(repolist)
    cache = cm()
    ready = cache.existsm(func=ctq, repos=repolist) == num_repos

    while not ready:
        time.sleep(1.0)
        ready = cache.existsm(func=ctq, repos=repolist) == num_repos

    start = time.perf_counter()
    logging.debug("CONTRIB_DRIVE_REPEAT_VIZ - START")

    # get all results from cache
    results = cache.getm(func=ctq, repos=repolist)

    # deserialize results, create list of dfs
    dfs = []
    for r in results:
        try:
            dfs.append(pd.read_csv(io.StringIO(r), sep=","))
        except:
            # some json lists are empty and aren't deserializable
            pass

    # aggregate dataframe from list of dfs
    df = pd.concat(dfs, ignore_index=True)

    # test if there is data
    if df.empty:
        logging.debug("CONTRIB DRIVE REPEAT - NO DATA AVAILABLE")
        return nodata_graph, False, dash.no_update

    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df.rename(columns={"created_at": "created"}, inplace=True)

    # graph on contribution subset
    contributors = df["cntrb_id"][df["rank"] == contribs].to_list()
    df_cont_subset = pd.DataFrame(df)

    # filtering data by view
    if view == "drive":
        df_cont_subset = df_cont_subset.loc[~df_cont_subset["cntrb_id"].isin(contributors)]
    else:
        df_cont_subset = df_cont_subset.loc[df_cont_subset["cntrb_id"].isin(contributors)]

    # reset index to be ready for plotly
    df_cont_subset = df_cont_subset.reset_index()

    # graph generation
    if df_cont_subset is not None:
        fig = px.histogram(df_cont_subset, x="created", color="Action", template="minty")
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
        logging.debug(f"CONTRIB_DRIVE_REPEAT_VIZ - END - {time.perf_counter() - start}")
        return fig
    else:
        return nodata_graph
