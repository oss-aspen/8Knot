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

gc_first_time_contributions = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Interval(
                    id="first-time-contributors-timer",
                    n_intervals=1,
                    max_intervals=1,
                    disabled=False,
                    interval=800,
                ),
                html.H4("First Time Contributions Per Quarter", className="card-title", style={"text-align": "center"}),
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
                dcc.Graph(id="first-time-contributions"),
                dbc.Row(
                    dbc.Button("About Graph", id="chaoss-popover-target-2", color="secondary", size="small"),
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
    Output("first-time-contributors-timer", "n_intervals"),
    [Input("repo-choices", "data"), Input("first-time-contributors-timer", "n_intervals")],
)
def create_first_time_contributors_graph(repolist, timer_pings):
    logging.debug("1ST_CONTRIBUTIONS_VIZ - START")

    ready, results, graph_update, interval_update = handle_job_state(jm, ctq, repolist)
    if not ready:
        return graph_update, interval_update

    start = time.perf_counter()

    df_cont = pd.DataFrame(results)

    # selection for 1st contribution only
    df_cont = df_cont[df_cont["rank"] == 1]

    # reset index to be ready for plotly
    df_cont = df_cont.reset_index()

    # Graph generation
    if df_cont is not None:
        fig = px.histogram(df_cont, x="created_at", color="Action", template="minty")
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
        logging.debug(f"1ST_CONTRIBUTIONS_VIZ - END - {time.perf_counter() - start}")
        return fig, dash.no_update
    else:
        return nodata_graph, dash.no_update
