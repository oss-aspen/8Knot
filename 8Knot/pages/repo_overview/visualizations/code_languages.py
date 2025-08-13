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
                html.H3(
                    id=f"graph-title-{PAGE}-{VIZ_ID}",
                    className="card-title",
                    style={"textAlign": "center"},
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
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Graph View:",
                                    html_for=f"graph-view-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
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
    # Handle empty dataframe case
    if df.empty:
        return pd.DataFrame(columns=["programming_language", "code_lines", "files", "Code %", "Files %"])
    
    # First, calculate the total lines and files BEFORE any modifications
    total_lines_original = df["code_lines"].sum()
    total_files_original = df["files"].sum()
    
    # Handle case where there are no files or lines
    if total_files_original == 0 or total_lines_original == 0:
        return pd.DataFrame(columns=["programming_language", "code_lines", "files", "Code %", "Files %"])

    # SVG files give one line of code per file
    # Note: Be careful with this - it modifies the actual line counts
    df.loc[df["programming_language"] == "SVG", "code_lines"] = df.loc[
        df["programming_language"] == "SVG", "files"
    ]

    # group files by their programming language and sum code lines and files
    df_lang = (
        df[["programming_language", "code_lines", "files"]]
        .groupby("programming_language")
        .sum()
        .reset_index()
    )

    # Handle case where groupby results in empty dataframe
    if df_lang.empty:
        return pd.DataFrame(columns=["programming_language", "code_lines", "files", "Code %", "Files %"])

    # Calculate percentages BEFORE grouping into "Other"
    # This preserves the true percentages
    total_lines_after_svg = df_lang["code_lines"].sum()
    total_files_after_svg = df_lang["files"].sum()
    
    # Use the totals after SVG modification for percentage calculation
    # but ensure we don't divide by zero
    if total_lines_after_svg > 0:
        df_lang["Code %"] = (df_lang["code_lines"] / total_lines_after_svg) * 100
    else:
        df_lang["Code %"] = 0
        
    if total_files_after_svg > 0:
        df_lang["Files %"] = (df_lang["files"] / total_files_after_svg) * 100
    else:
        df_lang["Files %"] = 0

    # Now group small languages into "Other"
    # require a language to have at least 0.1% of total files to be shown
    min_files = max(1, total_files_original / 1000)  # Ensure min_files is at least 1

    # Mark languages to be grouped as "Other"
    other_mask = df_lang["files"] <= min_files

    # Create an "Other" entry with the sum of all small languages
    if other_mask.any():
        other_data = df_lang[other_mask].sum()
        other_row = pd.DataFrame(
            {
                "programming_language": ["Other"],
                "code_lines": [other_data["code_lines"]],
                "files": [other_data["files"]],
                "Code %": [other_data["Code %"]],
                "Files %": [other_data["Files %"]],
            }
        )

        # Keep only the languages above threshold and add "Other"
        df_lang = pd.concat([df_lang[~other_mask], other_row], ignore_index=True)

    # Handle case where all languages got grouped into "Other" 
    # (shouldn't happen, but let's be safe)
    if df_lang.empty:
        df_lang = pd.DataFrame(
            {
                "programming_language": ["Other"],
                "code_lines": [total_lines_original],
                "files": [total_files_original],
                "Code %": [100.0],
                "Files %": [100.0],
            }
        )

    # order by descending file number
    df_lang = df_lang.sort_values(by="files", axis=0, ascending=False).reset_index(drop=True)

    return df_lang


def create_figure(df: pd.DataFrame, view):

    value = "files"
    if view == "line":
        value = "code_lines"

    # graph generation
    fig = px.pie(df, names="programming_language", values=value, color_discrete_sequence=color_seq)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Amount: %{value}<br><extra></extra>",
    )

    # add legend title
    fig.update_layout(legend_title_text="Languages")

    return fig
