from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
import numpy as np
import plotly.express as px
from utils.graph_utils import get_graph_time_values

gc_contributors_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("Contributor Types Over Time", className="card-title", style={"text-align": "center"}),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on graph 3"),
                    ],
                    id="chaoss-popover-3",
                    target="chaoss-popover-target-3",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="contributors-over-time")],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="contrib-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="contrib-time-interval",
                                        options=[
                                            {"label": "Day", "value": 86400000},  # days in milliseconds for ploty use
                                            {
                                                "label": "Week",
                                                "value": 604800000,
                                            },  # weeks in milliseconds for ploty use
                                            {"label": "Month", "value": "M1"},
                                            {"label": "Year", "value": "M12"},
                                        ],
                                        value="M1",
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph", id="chaoss-popover-target-3", color="secondary", size="sm"
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
                                    html_for="num_contribs_req",
                                    width={"size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="num_contribs_req",
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
    Output("chaoss-popover-3", "is_open"),
    [Input("chaoss-popover-target-3", "n_clicks")],
    [State("chaoss-popover-3", "is_open")],
)
def toggle_popover_3(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("contributors-over-time", "figure"),
    [
        Input("contributions", "data"),
        Input("num_contribs_req", "value"),
        Input("contrib-time-interval", "value"),
    ],
)
def create_graph(data, contribs, interval):
    logging.debug("CONTRIBUTIONS_OVER_TIME_VIZ - START")

    df_cont = pd.DataFrame(data)
    df_cont["created_at"] = pd.to_datetime(df_cont["created_at"], utc=True, format="%Y-%m-%d")

    # create column for identifying Drive by and Repeat Contributors
    contributors = df_cont["cntrb_id"][df_cont["rank"] == contribs].to_list()
    df_cont["type"] = np.where(df_cont["cntrb_id"].isin(contributors), "Repeat", "Drive-By")

    # reset index to be ready for plotly
    df_cont = df_cont.reset_index()

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graphs generated for aggregation by time interval
    drive_temp = (
        df_cont[df_cont["type"] == "Drive-By"]
        .groupby(by=df_cont.created_at.dt.to_period(period))["cntrb_id"]
        .nunique()
        .reset_index()
        .rename(columns={"cntrb_id": "Drive-By"})
    )
    repeat_temp = (
        df_cont[df_cont["type"] == "Repeat"]
        .groupby(by=df_cont.created_at.dt.to_period(period))["cntrb_id"]
        .nunique()
        .reset_index()
        .rename(columns={"cntrb_id": "Repeat"})
    )
    df_final = pd.merge(repeat_temp, drive_temp, on="created_at", how="outer")
    df_final["created_at"] = df_final["created_at"].dt.to_timestamp()

    # graph geration
    if df_final is not None:
        fig = px.histogram(
            df_final,
            x="created_at",
            y=[df_final["Repeat"], df_final["Drive-By"]],
            range_x=x_r,
            labels={"x": x_name, "y": "Contributors"},
            template="minty",
        )
        fig.update_traces(
            xbins_size=interval,
            hovertemplate=hover + "<br>Contributors: %{y}<br><extra></extra>",
        )
        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=interval,
            rangeslider_yaxis_rangemode="match",
        )
        fig.update_layout(
            xaxis_title=x_name,
            legend_title_text="Type",
            yaxis_title="Number of Contributors",
            margin_b=40,
        )
        logging.debug("CONTRIBUTIONS_OVER_TIME_VIZ - END")
        return fig
    else:
        return None
