from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import color_seq
from queries.commits_query import commits_query as cmq
import cache_manager.cache_facade as cf
from pages.utils.job_utils import nodata_graph
import time

PAGE = "contributors"
VIZ_ID = "contrib-activity-cycle"


gc_contrib_activity_cycle = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Contributor Activity Cycle",
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
                            Visualizes the distribution of Commit timestamps by Weekday or Hour.\n
                            Helps to describe operating-hours of community code contributions.
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
                    target=f"popover-target-{PAGE}-{VIZ_ID}",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
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
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Date Interval:",
                                            html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                            style={"marginBottom": "8px", "fontSize": "14px"},
                                        ),
                                        dbc.RadioItems(
                                            id=f"date-interval-{PAGE}-{VIZ_ID}",
                                            className="modern-radio-buttons-small",
                                            options=[
                                                {"label": "Weekday", "value": "D"},
                                                {"label": "Hourly", "value": "H"},
                                            ],
                                            value="D",
                                            inline=True,
                                        ),
                                    ],
                                    width="auto",
                                ),
                            ],
                            justify="start",
                        ),
                    ]
                ),
            ]
        )
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


# callback for VIZ TITLE graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def contrib_activity_cycle_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=cmq.__name__, repolist=repolist):
        logging.warning(f"COMMITS_OVER_TIME_VIZ - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=cmq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, interval)

    fig = create_figure(df, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
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
        weekday = pd.concat(
            [
                df["author_timestamp"].dt.day_name(),
                df["committer_timestamp"].dt.day_name(),
            ]
        )
        df_weekday = pd.DataFrame(weekday, columns=["Weekday"])
        df_final = df_weekday.groupby(["Weekday"])["Weekday"].count()

    return df_final


def create_figure(df: pd.DataFrame, interval):
    column = "Weekday"
    order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    if interval == "H":
        column = "Hour"

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
        plot_bgcolor="#292929",
        paper_bgcolor="#292929",
    )

    return fig
