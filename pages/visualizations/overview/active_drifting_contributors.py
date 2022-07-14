from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from utils.graph_utils import get_graph_time_values

gc_active_drifting_contributors = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    "Contributor Growth by Engagement",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "<ACTIVE> contributors have contributed within last 6 months.\n\
                            <DRIFTING> contributors have contributed within last year but are not active.\n\
                            <AWAY> contributors haven't made any contributions in the last year at least."
                        ),
                    ],
                    id="overview-popover-4",
                    target="overview-popover-target-4",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="active_drifting_contributors")],
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
                                    html_for="active-drifting-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id="active-drifting-interval",
                                            options=[
                                                {
                                                    "label": "Day",
                                                    "value": "D",
                                                },  # days in milliseconds for ploty use
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
                                            inline=True,
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-4",
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
                                    "Months Until Drifting:",
                                    html_for="drifting_months",
                                    width={"size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="drifting_months",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=6,
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "Months Until Away:",
                                    html_for="away_months",
                                    width={"size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="away_months",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=12,
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Alert(
                            children="Please ensure that 'Months Until Drifting' is less than 'Months Until Away'",
                            id="drifting_away_check_alert",
                            dismissable=True,
                            fade=False,
                            is_open=False,
                            color="warning",
                        ),
                    ]
                ),
            ]
        )
    ],
    color="light",
)

# call backs for card graph 4 - Active Drifting Away Over Time
@callback(
    Output("overview-popover-4", "is_open"),
    [Input("overview-popover-target-4", "n_clicks")],
    [State("overview-popover-4", "is_open")],
)
def toggle_popover_4(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("active_drifting_contributors", "figure"),
    Output("drifting_away_check_alert", "is_open"),
    [
        Input("contributions", "data"),
        Input("active-drifting-interval", "value"),
        Input("drifting_months", "value"),
        Input("away_months", "value"),
    ],
)
def active_drifting_contributors(df, interval, drift_interval, away_interval):

    if drift_interval > away_interval:
        return dash.no_update, True

    if drift_interval is None or away_interval is None:
        return dash.no_update, dash.no_update

    df = pd.DataFrame(df)

    # order from beginning of time to most recent
    df = df.sort_values("created_at", axis=0, ascending=True)

    # convert to datetime objects
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df.iloc[0]["created_at"]
    latest = df.iloc[-1]["created_at"]

    # beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    base = [["Date", "Active", "Drifting", "Away"]]
    for date in dates:
        counts = get_active_drifting_away_up_to(df, date, drift_interval, away_interval)
        base.append(counts)

    df_status = pd.DataFrame(base[1:], columns=base[0])

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # making a line graph if the bin-size is small enough.
    if interval == "D":
        fig = go.Figure(
            [
                go.Scatter(
                    name="Active",
                    x=df_status["Date"],
                    y=df_status["Active"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors Active: %{y}" + "<extra></extra>",
                ),
                go.Scatter(
                    name="Drifting",
                    x=df_status["Date"],
                    y=df_status["Drifting"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors Drifting: %{y}" + "<extra></extra>",
                ),
                go.Scatter(
                    name="Away",
                    x=df_status["Date"],
                    y=df_status["Away"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors Away: %{y}" + "<extra></extra>",
                ),
            ]
        )
    else:
        fig = px.bar(df_status, x="Date", y=["Active", "Drifting", "Away"])

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>Contributors: %{y}<br>" + "<extra></extra>")

    fig.update_layout(xaxis_title="Time", yaxis_title="Number of Contributors")
    return fig, False


def get_active_drifting_away_up_to(df, date, drift_interval, away_interval):

    # drop rows that are more recent than the date limit
    df_lim = df[df["created_at"] <= date]

    # keep more recent contribution per ID
    df_lim = df_lim.drop_duplicates(subset="cntrb_id", keep="last")

    # time difference, 6 months before the threshold date
    drift_mos = date - relativedelta(months=+drift_interval)

    # time difference, 6 months before the threshold date
    away_mos = date - relativedelta(months=+away_interval)

    # contributions in the last 6 months
    numTotal = df_lim.shape[0]

    numActive = df_lim[df_lim["created_at"] >= drift_mos].shape[0]

    drifting = df_lim[df_lim["created_at"] > away_mos]
    numDrifting = drifting[drifting["created_at"] < drift_mos].shape[0]

    numAway = numTotal - (numActive + numDrifting)

    return [date, numActive, numDrifting, numAway]
