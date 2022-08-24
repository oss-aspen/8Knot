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

gc_pr_staleness = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    "Pull Request Activity- Staleness",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "<NEW> Pull Requests actively open within the lower time varible.\n\
                            <DRIFT> Pull Requests actively open between the two time varibles.\n\
                            <STALE> Pull Requests actively open after the upper time varible."
                        ),
                    ],
                    id="overview-popover-prs",
                    target="overview-popover-target-prs",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="pr_staleness")],
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
                                    html_for="pr-staleness-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id="pr-staleness-interval",
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
                                        id="overview-popover-target-prs",
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
                                    "Days Until Drift:",
                                    html_for="drift_days",
                                    width={"size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="drift_days",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=7,
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "Days Until Stale:",
                                    html_for="stale_days",
                                    width={"size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id="stale_days",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=30,
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Alert(
                            children="Please ensure that 'Days Until Drift' is less than 'Days Until Stale'",
                            id="drift_stale_check_alert",
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


@callback(
    Output("overview-popover-prs", "is_open"),
    [Input("overview-popover-target-prs", "n_clicks")],
    [State("overview-popover-prs", "is_open")],
)
def toggle_popover_prs(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("pr_staleness", "figure"),
    Output("drift_stale_check_alert", "is_open"),
    [
        Input("pr-data", "data"),
        Input("pr-staleness-interval", "value"),
        Input("drift_days", "value"),
        Input("stale_days", "value"),
    ],
)
def new_drifting_prs(df, interval, drift_interval, stale_interval):
    logging.debug("ISSUE STALENESS - START")

    if drift_interval > stale_interval:
        return dash.no_update, True

    if drift_interval is None or stale_interval is None:
        return dash.no_update, dash.no_update

    df = pd.DataFrame(df)
    print(df[:10])

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df.iloc[0]["created"]
    latest = df.iloc[-1]["created"]

    # generating buckets beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")

    base = [["Date", "New", "Drift", "Stale"]]
    for date in dates:
        counts = get_new_drifting_stale_up_to(df, date, drift_interval, stale_interval)
        base.append(counts)
    print("here")

    df_status = pd.DataFrame(base[1:], columns=base[0])

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # making a line graph if the bin-size is small enough.
    if interval == "D":
        fig = go.Figure(
            [
                go.Scatter(
                    name="New",
                    x=df_status["Date"],
                    y=df_status["New"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors New: %{y}" + "<extra></extra>",
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
                    name="Stale",
                    x=df_status["Date"],
                    y=df_status["Stale"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors Stale: %{y}" + "<extra></extra>",
                ),
            ]
        )
    else:
        fig = px.bar(df_status, x="Date", y=["New", "Drifting", "Stale"])

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>Contributors: %{y}<br>" + "<extra></extra>")

    fig.update_layout(xaxis_title="Time", yaxis_title="Number of Contributors")

    logging.debug("ISSUE STALENESS - END")
    return fig, False


def get_new_drifting_stale_up_to(df, date, drift_interval, stale_interval):

    # drop rows that are more recent than the date limit
    df_lim_created = df[df["created"] <= date]

    # drop rows that have been closed before date
    df_lim = df_lim_created[df_lim_created["closed"] > date]

    # time difference for the amount of days before the threshold date
    drift_days = date - relativedelta(days=+drift_interval)

    # time difference for the amount of days before the threshold date
    stale_days = date - relativedelta(days=+stale_interval)

    # PRs still open at the specified date
    numTotal = df_lim.shape[0]

    # num of currently open PRs that have been create in the last drift_value amount of days
    numNew = df_lim[df_lim["created"] >= drift_days].shape[0]

    drifting = df_lim[df_lim["created"] > stale_days]
    numDrifting = drifting[drifting["created"] < drift_days].shape[0]

    numStale = numTotal - (numNew + numDrifting)

    return [date, numNew, numDrifting, numStale]
