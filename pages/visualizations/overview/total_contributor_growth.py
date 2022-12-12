from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.contributors_query import contributors_query as ctq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph

import time

gc_total_contributor_growth = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    id="overview-graph-title-1",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on graph 1"),
                    ],
                    id="overview-popover-1",
                    target="overview-popover-target-1",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id="total_contributor_growth"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval",
                                    html_for="contributor-growth-time-interval",
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="contributor-growth-time-interval",
                                        options=[
                                            {
                                                "label": "Trend",
                                                "value": -1,
                                            },
                                            {"label": "Month", "value": "M"},
                                            {"label": "Year", "value": "Y"},
                                        ],
                                        value="M",
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-1",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
    # color="light",
)


# call backs for card graph 1 - total contributor growth
@callback(
    Output("overview-popover-1", "is_open"),
    [Input("overview-popover-target-1", "n_clicks")],
    [State("overview-popover-1", "is_open")],
)
def toggle_popover_1(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("overview-graph-title-1", "children"),
    Input("contributor-growth-time-interval", "value"),
)
def graph_title(view):
    title = ""
    if view == -1:
        title = "Total Contributors Over Time"
    elif view == "M":
        title = "New Contributors by Month"
    else:
        title = "New Contributors by Year"
    return title


@callback(
    Output("total_contributor_growth", "figure"),
    [
        Input("repo-choices", "data"),
        Input("contributor-growth-time-interval", "value"),
    ],
    background=True,
)
def total_contributor_growth_graph(repolist, interval):

    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    logging.debug("TOTAL_CONTRIBUTOR_GROWTH_VIZ - START")
    start = time.perf_counter()

    # test if there is data
    if df.empty:
        logging.debug("TOTAL_CONTRIBUTOR_GROWTH_VIZ - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df, df_contribs = process_data(df, interval)

    fig = create_figure(df, df_contribs, interval)

    logging.debug(f"TOTAL_CONTRIBUTOR_GROWTH_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df, interval):

    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df.rename(columns={"created_at": "created"}, inplace=True)

    # order from beginning of time to most recent
    df = df.sort_values("created", axis=0, ascending=True)

    """
        Assume that the cntrb_id values are unique to individual contributors.
        Find the first rank-1 contribution of the contributors, saving the created
        date.
    """

    # keep only first contributions
    df = df[df["rank"] == 1]

    # get all of the unique entries by contributor ID
    df.drop_duplicates(subset=["cntrb_id"], inplace=True)
    df.reset_index(inplace=True)

    if interval == -1:
        return df, None

    # get the count of new contributors in the desired interval in pandas period format, sort index to order entries
    created_range = pd.to_datetime(df["created"]).dt.to_period(interval).value_counts().sort_index()

    # converts to data frame object and creates date column from period values
    df_contribs = created_range.to_frame().reset_index().rename(columns={"index": "Date", "created": "contribs"})

    # converts date column to a datetime object, converts to string first to handle period information
    df_contribs["Date"] = pd.to_datetime(df_contribs["Date"].astype(str))

    # correction for year binning -
    # rounded up to next year so this is a simple patch
    if interval == "Y":
        df_contribs["Date"] = df_contribs["Date"].dt.year
    elif interval == "M":
        df_contribs["Date"] = df_contribs["Date"].dt.strftime("%Y-%m")

    return df, df_contribs


def create_figure(df, df_contribs, interval):

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    if interval == -1:
        fig = px.line(df, x="created", y=df.index, color_discrete_sequence=[color_seq[3]])
        fig.update_traces(hovertemplate="Contributors: %{y}<br>%{x|%b %d, %Y} <extra></extra>")
    else:
        fig = px.bar(
            df_contribs,
            x="Date",
            y="contribs",
            range_x=x_r,
            labels={"x": x_name, "y": "Contributors"},
            color_discrete_sequence=[color_seq[3]],
        )
        fig.update_traces(hovertemplate=hover + "<br>Contributors: %{y}<br>")

    """
        Ref. for this awesome button thing:
        https://plotly.com/python/range-slider/
    """
    # add the date-range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )
    # label the figure correctly
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Contributors",
        margin_b=40,
        margin_r=20,
        font=dict(size=14),
    )
    return fig
