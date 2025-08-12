from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import baby_blue
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
                        dbc.Col(html.H3(id=f"graph-title-{PAGE}-{VIZ_ID}", className="card-title")),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                color="outline-secondary",
                                size="sm",
                                className="about-graph-button",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    justify="between",
                    className="mb-3",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes the percent of files or lines of code by language.
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
                    style={"marginBottom": "1rem"},
                ),
                html.Hr(  # Divider between graph and controls
                    style={
                        "borderColor": "#909090",
                        "margin": "1.5rem -1.5rem",
                        "width": "calc(100% + 3rem)",
                    }
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Graph View:",
                                            html_for=f"graph-view-{PAGE}-{VIZ_ID}",
                                            style={"fontSize": "12px", "fontWeight": "bold", "marginBottom": "0.5rem"},
                                        ),
                                        dbc.RadioItems(
                                            id=f"graph-view-{PAGE}-{VIZ_ID}",
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
                                            className="custom-radio-buttons",
                                        ),
                                    ],
                                    width="auto",
                                ),
                            ],
                            align="center",
                            justify="between",
                            className="mb-0",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},  # Padding between main content and the card border
        )
    ],
    className="dark-card",
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

    # graph generation
    fig = px.pie(df, names="programming_language", values=value, color_discrete_sequence=baby_blue)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Amount: %{value}<br><extra></extra>",
    )

    # add legend title
    fig.update_layout(
        legend_title_text="Languages",
        paper_bgcolor="#292929",
        plot_bgcolor="#292929",
        font=dict(color="white"),  # Makes all text white
        legend=dict(font=dict(color="white")),  # Specifically makes legend text white
    )

    return fig
