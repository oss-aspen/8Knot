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
from queries.repo_languages_query import repo_languages_query as rlq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import cache_manager.cache_facade as cf

PAGE = "repo_info"
VIZ_ID = "code-languages"

gc_code_language = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                id=f"graph-title-{PAGE}-{VIZ_ID}",
                                className="card-title",
                                style={"textAlign": "left", "fontSize": "20px"},
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
                            Visualizes the percent of files or lines of code by language.
                            """,
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
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                html.Hr(style={
                    "borderColor": "#e0e0e0", 
                    "margin": "1.5rem -2rem", 
                    "width": "calc(100% + 4rem)",
                    "marginLeft": "-2rem"
                }),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Graph View:",
                                            html_for=f"graph-view-{PAGE}-{VIZ_ID}",
                                            style={"marginBottom": "8px", "fontSize": "14px"}
                                        ),
                                        dbc.RadioItems(
                                            id=f"graph-view-{PAGE}-{VIZ_ID}",
                                            className="modern-radio-buttons-small",
                                            options=[
                                                {
                                                    "label": "Files",
                                                    "value": "file",
                                                },
                                                {
                                                    "label": "Lines of Code",
                                                    "value": "line",
                                                },
                                            ],
                                            value="file",
                                            inline=True,
                                        ),
                                    ],
                                    width="auto"
                                ),
                            ],
                            justify="start",
                        ),
                    ]
                ),
            ],
            style={"padding": "2rem"}
        )
    ],
    style={"backgroundColor": "#292929", "borderRadius": "15px", "border": "1px solid #404040"}
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


# callback for dynamically changing the graph title
@callback(
    Output(f"graph-title-{PAGE}-{VIZ_ID}", "children"),
    Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
)
def graph_title(view):
    title = ""
    if view == "file":
        title = "File Language by File"
    else:
        title = "File Language by Line"
    return title


# callback for code languages graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def code_languages_graph(repolist, view):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=rlq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=rlq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df = process_data(df)

    fig = create_figure(df, view)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame):

    # SVG files give one line of code per file
    df.loc[df["programming_language"] == "SVG", "code_lines"] = df["files"]

    # group files by their programing language and sum code lines and files
    df_lang = df[["programming_language", "code_lines", "files"]].groupby("programming_language").sum().reset_index()

    # require a language to have atleast .1 % of total files to be shown, if not grouped into other
    min_files = df_lang["files"].sum() / 1000
    df_lang.loc[df_lang.files <= min_files, "programming_language"] = "Other"
    df_lang = (
        df_lang[["programming_language", "code_lines", "files"]].groupby("programming_language").sum().reset_index()
    )

    # order by descending file number and reset format
    df_lang = df_lang.sort_values(by="files", axis=0, ascending=False).reset_index()
    df_lang.drop("index", axis=1, inplace=True)

    # calculate percentages
    df_lang["Code %"] = (df_lang["code_lines"] / df_lang["code_lines"].sum()) * 100
    df_lang["Files %"] = (df_lang["files"] / df_lang["files"].sum()) * 100

    return df_lang


def create_figure(df: pd.DataFrame, view):

    value = "files"
    if view == "line":
        value = "code_lines"

    # Blue gradient color scheme starting with white but transitioning to blue more quickly
    blue_gradient_colors = [
        "#FFFFFF",  # Pure white
        "#E6F3FF",  # Very light blue
        "#B3D9FF",  # Light blue - faster transition
        "#80BFFF",  # Light blue
        "#76C5EF",  # Medium blue (from package graph)
        "#4DA6FF",  # Medium blue
        "#2E9FDB",  # Medium blue
        "#199AD6",  # Medium dark blue (from package graph)
        "#1485C2",  # Medium dark blue
        "#0F70AE",  # Dark blue
        "#0F5880",  # Dark blue (from package graph)
        "#0A4460",  # Very dark blue
        "#053040",  # Very dark blue
        "#02141C"   # Very dark blue
    ]

    # graph generation
    fig = px.pie(df, names="programming_language", values=value, color_discrete_sequence=blue_gradient_colors)
    fig.update_traces(
        domain=dict(x=[0, 0.45]),  # Keep original pie chart size
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Amount: %{value}<br><extra></extra>",
    )

    # add legend title and dark theme styling with vertical layout
    fig.update_layout(
        legend_title_text="Languages",
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

    return fig
