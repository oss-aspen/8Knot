from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
import plotly.express as px

from app import jm
from pages.utils.job_utils import handle_job_state, nodata_graph
from queries.contributors_query import contributors_query as ctq
import time

gc_contrib_drive_repeat = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Interval(
                    id="contrib-drive-repeat-timer",
                    n_intervals=1,
                    max_intervals=1,
                    disabled=False,
                    interval=800,
                ),
                html.H4(id="chaoss-graph-title-1", className="card-title", style={"text-align": "center"}),
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
                dcc.Graph(id="cont-drive-repeat"),
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
                                        "About Graph", id="chaoss-popover-target-1", color="secondary", size="sm"
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
    Output("contrib-drive-repeat-timer", "n_intervals"),
    [
        Input("repo-choices", "data"),
        Input("contrib-drive-repeat-timer", "n_intervals"),
        Input("num_contributions", "value"),
        Input("drive-repeat", "value"),
    ],
)
def create_drive_by_graph(repolist, timer_pings, contribs, view):
    logging.debug("CDR - PONG")

    ready, results, graph_update, interval_update = handle_job_state(jm, ctq, repolist)
    if not ready:
        return graph_update, interval_update

    logging.debug("CONTRIB_DRIVE_REPEAT_VIZ - START")
    start = time.perf_counter()

    # graph on contribution subset
    df_cont = pd.DataFrame(results)
    contributors = df_cont["cntrb_id"][df_cont["rank"] == contribs].to_list()
    df_cont_subset = pd.DataFrame(results)

    # filtering data by view
    if view == "drive":
        df_cont_subset = df_cont_subset.loc[~df_cont_subset["cntrb_id"].isin(contributors)]
    else:
        df_cont_subset = df_cont_subset.loc[df_cont_subset["cntrb_id"].isin(contributors)]

    # reset index to be ready for plotly
    df_cont_subset = df_cont_subset.reset_index()

    # graph geration
    if df_cont_subset is not None:
        fig = px.histogram(df_cont_subset, x="created_at", color="Action", template="minty")
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
        return fig, dash.no_update
    else:
        return nodata_graph, dash.no_update
