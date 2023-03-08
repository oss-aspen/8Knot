from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.commits_query import commits_query as cmq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time

PAGE = "chaoss"  # EDIT FOR PAGE USED
VIZ_ID = "contrib-activity-cycle"  # UNIQUE IDENTIFIER FOR CALLBAKCS, MUST BE UNIQUE


gc_contrib_activity_cycle = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor Activity Cycle",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This graph looks at the the timestamps of commits being created and\n\
                                        when they are commited to the code base. This gives a view on the activity cycle\n\
                                        of you contributor base."
                        ),
                    ],
                    id=f"{PAGE}-popover-{VIZ_ID}",
                    target=f"{PAGE}-popover-target-{VIZ_ID}",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=VIZ_ID),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"{VIZ_ID}-interval",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"{VIZ_ID}-interval",
                                            options=[
                                                {
                                                    "label": "Weekday",
                                                    "value": "D",
                                                },
                                                {"label": "Hourly", "value": "H"},
                                            ],
                                            value="D",
                                            inline=True,
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"{PAGE}-popover-target-{VIZ_ID}",
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
        )
    ],
)

# callback for graph info popover
@callback(
    Output(f"{PAGE}-popover-{VIZ_ID}", "is_open"),
    [Input(f"{PAGE}-popover-target-{VIZ_ID}", "n_clicks")],
    [State(f"{PAGE}-popover-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for VIZ TITLE graph
@callback(
    Output(VIZ_ID, "figure"),
    [
        Input("repo-choices", "data"),
        Input(VIZ_ID + "-interval", "value"),
    ],
    background=True,
)
def contrib_activity_cycle_graph(repolist, interval):

    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=cmq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=cmq, repos=repolist)

    start = time.perf_counter()
    logging.debug(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.debug(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.debug(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):

    # for this usecase we want the datetimes to be in their local values
    # tricking pandas to keep local values when UTC conversion is required for to_datetime
    df["author_timestamp"] = df["author_timestamp"].astype("str").str[:-6]
    df["committer_timestamp"] = df["committer_timestamp"].astype("str").str[:-6]

    # convert to datetime objects rather than strings
    df["author_timestamp"] = pd.to_datetime(df["author_timestamp"], utc=True)
    df["committer_timestamp"] = pd.to_datetime(df["committer_timestamp"], utc=True)
    # removes duplicate values when the author and committer is the same
    df.loc[df["author_timestamp"] == df["committer_timestamp"], "author_timestamp"] = None

    df_final = pd.DataFrame()

    if interval == "H":
        # combine the hour values for author and committer
        hour = pd.concat([df["author_timestamp"].dt.hour, df["committer_timestamp"].dt.hour])
        df_hour = pd.DataFrame(hour, columns=["Hour"])
        df_final = df_hour.groupby(["Hour"])["Hour"].count()
    else:
        # combine the weekday values for author and committer
        weekday = pd.concat([df["author_timestamp"].dt.day_name(), df["committer_timestamp"].dt.day_name()])
        df_weekday = pd.DataFrame(weekday, columns=["Weekday"])
        df_final = df_weekday.groupby(["Weekday"])["Weekday"].count()

    # code for the histogram option for the workshop - will remove when pushing to dev
    """weekday = pd.concat([df["author_timestamp"].dt.day_name(), df["committer_timestamp"].dt.day_name()])
    hour = pd.concat([df["author_timestamp"].dt.hour, df["committer_timestamp"].dt.hour])
    df_final = pd.DataFrame(weekday, columns=["Weekday"])
    df_final["Hour"] = hour"""

    return df_final


def create_figure(df: pd.DataFrame, interval):

    column = "Weekday"
    order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    if interval == "H":
        column = "Hour"

    # code for the histogram option for the workshop - will remove when pushing to dev
    """fig = px.histogram(df, x=column, color_discrete_sequence=[color_seq[3]])
    if interval == "D":
        fig.update_xaxes(
            categoryorder="array",
            categoryarray=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        )
    fig.update_layout(
        yaxis_title="Activity Count",
        font=dict(size=14),
    )"""

    fig = px.bar(df, y=column, color_discrete_sequence=[color_seq[3]])
    hover = "%{x} Activity Count: %{y}<br>"
    if interval == "H":
        hover = "Hour: %{x}:00 Activity Count: %{y}<br>"
    fig.update_traces(hovertemplate=hover)
    fig.update_xaxes(
        categoryorder="array",
        categoryarray=order,
    )
    fig.update_layout(
        yaxis_title="Activity Count",
        xaxis_title=column,
        font=dict(size=14),
    )

    return fig
