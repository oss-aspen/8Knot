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
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Package Version Updates",
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
                                    "boxShadow": "none"
                                }
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
                                "padding": "12px 16px"
                            }
                        ),
                        dbc.PopoverBody(
                            """
                            Visualizes for each packaged dependancy, if it is up to date and if not if it is
                            less than 6 months out, between 6 months and a year, or greater than a year.
                            """
                        ,
                            style={
                                "backgroundColor": "#292929",
                                "color": "#E0E0E0",
                                "border": "none",
                                "fontSize": "14px",
                                "lineHeight": "1.5",
                                "padding": "16px"
                            }
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,

                    style={
                        "backgroundColor": "#292929",
                        "border": "1px solid #606060",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.3)",
                        "maxWidth": "400px"
                    }

                    ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
            ],
            style={"padding": "2rem"}
        )
    ],
    style={"backgroundColor": "#292929", "borderRadius": "15px", "border": "1px solid #404040"},
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

    # count the number of each package grouping
    df = pd.DataFrame(df["dep_age"].value_counts().reset_index())

    # graph generation
    custom_colors = ["#DFF0FB", "#76C5EF", "#199AD6", "#0F5880"]
    fig = px.pie(df, names="dep_age", values="count", color_discrete_sequence=custom_colors)
    fig.update_traces(
        domain=dict(x=[0, 0.45]),
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Packages: %{value}<br><extra></extra>",
    )

    fig.update_layout(
        plot_bgcolor="#292929",
        paper_bgcolor="#292929",
        legend=dict(
            orientation="v",
            x=0.42,  # Legend starts right after the pie chart
            y=0.5,
            xanchor="left",
            yanchor="middle"
        ),
        font=dict(
            family="Inter, sans-serif",  # Font family
            size=14,                     # Font size
            color="white"                # Font color
        ),
        margin=dict(r=50, l=50, t=50, b=50)
    )
    
    fig["layout"]["legend_title"] = "Date Range"

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig
