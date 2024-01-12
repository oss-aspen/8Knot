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
from queries.package_version_query import package_version_query as pvq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import cache_manager.cache_facade as cf

PAGE = "repo_info"
VIZ_ID = "package-version"

gc_package_version = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Package Version Updates",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes for each packaged dependancy, if it is up to date and if not if it is
                            less than 6 months out, between 6 months and a year, or greater than a year.
                            """
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
                            justify="end",
                        ),
                    ]
                ),
            ]
        )
    ],
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


# callback for package version updates graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
    ],
    background=True,
)
def package_version_graph(repolist):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=pvq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=pvq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df = process_data(df)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame):

    # get max time difference to use for grouping and round for correct format
    max_time = round(df["libyear"].max(), 3)

    # group by the 4 buckets
    depend_pie = pd.DataFrame(
        df["libyear"].groupby(pd.cut(df["libyear"], [0, 0.001, 0.5, 1, max_time], right=False)).count()
    ).rename(columns={"libyear": "packages"})
    depend_pie = depend_pie.reset_index().rename(columns={"libyear": "date_range"})
    depend_pie["date_range"] = depend_pie["date_range"].astype(str)

    # create string for naming
    max_string = "[1.0, " + str(max_time) + ")"

    # update naming for pie chart
    depend_pie.loc[depend_pie["date_range"] == "[0.0, 0.001)", "date_range"] = "Up to date"
    depend_pie.loc[depend_pie["date_range"] == "[0.001, 0.5)", "date_range"] = "Less than 6 months"
    depend_pie.loc[depend_pie["date_range"] == "[0.5, 1.0)", "date_range"] = "6 months to year"
    depend_pie.loc[depend_pie["date_range"] == max_string, "date_range"] = "Greater than a year"

    return depend_pie


def create_figure(df: pd.DataFrame):

    # graph generation
    fig = px.pie(df, names="date_range", values="packages", color_discrete_sequence=color_seq)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Packages: %{value}<br><extra></extra>",
    )

    # add legend title
    fig["layout"]["legend_title"] = "Date Range"

    return fig
