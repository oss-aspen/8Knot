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

gc_first_time_contributions = dbc.Card(
    [
        dbc.CardBody(
            [
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
                dcc.Loading(
                    children=[dcc.Graph(id="first-time-contributions")],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
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


@callback(Output("first-time-contributions", "figure"), Input("contributions", "data"))
def create_first_time_contributors_graph(data):
    logging.debug("1ST_CONTRIBUTIONS_VIZ - START")
    df_cont = pd.DataFrame(data)

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
        logging.debug("1ST_CONTRIBUTIONS_VIZ - END")
        return fig
    else:
        return None
