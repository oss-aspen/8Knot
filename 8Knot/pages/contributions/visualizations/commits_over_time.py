from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.commits_query import commits_query as cmq
from pages.utils.job_utils import nodata_graph
import time
import cache_manager.cache_facade as cf

PAGE = "contributions"
VIZ_ID = "commits-over-time"

gc_commits_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Commits Over Time",
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
                            Visualizes the number of commits added to the project.\n
                            Commits are counted relative to a user-selected time window.
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
                                                {"label": "Day", "value": "D"},
                                                {"label": "Week", "value": "W"},
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
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
        ),
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


# callback for commits over time graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def commits_over_time_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=cmq.__name__, repolist=repolist):
        logging.warning(f"COMMITS_OVER_TIME_VIZ - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # data ready.
    start = time.perf_counter()
    logging.warning("COMMITS_OVER_TIME_VIZ - START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=cmq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning("COMMITS OVER TIME - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df_created = process_data(df, interval)

    fig = create_figure(df_created, interval)

    logging.warning(f"COMMITS_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    # convert to datetime objects with consistent column name
    # incoming value should be a posix integer.
    df["author_date"] = pd.to_datetime(df["author_date"], utc=True)
    df.rename(columns={"author_date": "created_at"}, inplace=True)

    # variable to slice on to handle weekly period edge case
    period_slice = None
    if interval == "W":
        # this is to slice the extra period information that comes with the weekly case
        period_slice = 10

    # get the count of commits in the desired interval in pandas period format, sort index to order entries
    df_created = (
        df.groupby(by=df.created_at.dt.to_period(interval))["commit_hash"]
        .nunique()
        .reset_index()
        .rename(columns={"created_at": "Date"})
    )

    # converts date column to a datetime object, converts to string first to handle period information
    # the period slice is to handle weekly corner case
    df_created["Date"] = pd.to_datetime(df_created["Date"].astype(str).str[:period_slice])

    return df_created


def create_figure(df_created: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph geration
    fig = px.bar(
        df_created,
        x="Date",
        y="commit_hash",
        range_x=x_r,
        labels={"x": x_name, "y": "Commits"},
        color_discrete_sequence=[color_seq[3]],
    )
    fig.update_traces(hovertemplate=hover + "<br>Commits: %{y}<br>")
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        rangeslider_yaxis_rangemode="match",
        range=x_r,
    )
    fig.update_layout(
        xaxis_title=x_name,
        yaxis_title="Number of Commits",
        margin_b=40,
        margin_r=20,
        font=dict(size=14),
        plot_bgcolor="#292929",
        paper_bgcolor="#292929",
    )

    return fig
