from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.repo_info_query import repo_info_query as riq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time

PAGE = "starter-project-health"
VIZ_ID = "fork-count"

gc_fork_count_graph = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    id=f"graph-title-{PAGE}-{VIZ_ID}",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "Visualizes the growth of contributor base by tracking the arrival of novel contributors over time.\n\
                            Trend: This view is the total growth of contributors over time \n\
                            Month/Year: This view looks specifically at the new contributors by selected time bucket."
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval",
                                    html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id=f"date-interval-{PAGE}-{VIZ_ID}",
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
                                        id=f"popover-target-{PAGE}-{VIZ_ID}",
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
        ),
    ],
)


# callback for graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover_1(n, is_open):
    if n:
        return not is_open
    return is_open


# callback to dynamically change the graph title
@callback(
    Output(f"graph-title-{PAGE}-{VIZ_ID}", "children"),
    Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
)
def graph_title(view):
    title = ""
    if view == -1:
        title = "Total Forks Over Time"
    elif view == "M":
        title = "New Forks by Month"
    else:
        title = "New Forks by Year"
    return title


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def fork_count_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=riq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=riq, repos=repolist)

    logging.warning("FORK_COUNT_VIZ - START")
    start = time.perf_counter()

    # test if there is data
    if df.empty:
        logging.warning("FORK_COUNT_VIZ - NO DATA AVAILABLE")    
        return nodata_graph

    # function for all data pre processing
    df, df_contribs = process_data(df, interval)

    fig = create_figure(df, df_contribs, interval)

    logging.warning(f"FORK_COUNT_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df, interval):
    # convert to datetime objects with consistent column name
    #convert dates to datetimes for ease of processing
    df["last_updated"] = pd.to_datetime(df["last_updated"], utc=True)
    df.rename(columns={"last_updated": "created"}, inplace=True)

    # order from beginning of time to most recent
    df = df.sort_values("created", axis=0, ascending=True)

    df1 = df[['created', 'fork_count']]

    """
        Assume that the cntrb_id values are unique to individual contributors.
        Find the first rank-1 contribution of the contributors, saving the created
        date.
    """

    logging.warning(df1.head())

    if interval == -1:
        return df1, None

    # get the count of new contributors in the desired interval in pandas period format, sort index to order entries
    created_range = pd.to_datetime(df1["created"]).dt.to_period(interval).value_counts().sort_index()

    # converts to data frame object and creates date column from period values
    df1_contribs = created_range.to_frame().reset_index().rename(columns={"index": "Date", "created": "contribs"})

    # converts date column to a datetime object, converts to string first to handle period information
    df1_contribs["Date"] = pd.to_datetime(df1_contribs["Date"].astype(str))

    # correction for year binning -
    # rounded up to next year so this is a simple patch
    if interval == "Y":
        df1_contribs["Date"] = df1_contribs["Date"].dt.year
    elif interval == "M":
        df1_contribs["Date"] = df1_contribs["Date"].dt.strftime("%Y-%m")

    return df1, df1_contribs


def create_figure(df, df_contribs, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    if interval == -1:
        fig = px.line(df, x="created", y=df.index, color_discrete_sequence=[color_seq[3]])
        fig.update_traces(hovertemplate="Forks: %{y}<br>%{x|%b %d, %Y} <extra></extra>")
    else:
        fig = px.bar(
            df_contribs,
            x="Date",
            y="contribs",
            range_x=x_r,
            labels={"x": x_name, "y": "Forks"},
            color_discrete_sequence=[color_seq[3]],
        )
        fig.update_traces(hovertemplate=hover + "<br>Forks: %{y}<br>")

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
        yaxis_title="Number of Forks",
        margin_b=40,
        margin_r=20,
        font=dict(size=14),
    )
    return fig
