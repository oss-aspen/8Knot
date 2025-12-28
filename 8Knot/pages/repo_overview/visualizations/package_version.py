from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from typing import List, Optional, Tuple, Union
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import baby_blue
from queries.package_version_query import package_version_query as pvq
from pages.utils.job_utils import nodata_graph
from pages.utils.query_status import load_query_data
import datetime as dt
from components.visualization import VisualizationAIO

PAGE = "repo_info"
VIZ_ID = "package-version"

gc_package_version = VisualizationAIO(
    PAGE,
    VIZ_ID,
    title="Package Version Updates",
    graph_info="""
        Visualizes for each packaged dependency, if it is up to date and if not if it is
        less than 6 months out, between 6 months and a year, or greater than a year.
    """,
    controls=[],
    class_name="dark-card",
    id="package-version",
)


# callback for package version updates graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
    ],
    background=True,
)
def package_version_graph(repolist):
    # Wait for and load query data (includes timeout, error handling, and validation)
    df = load_query_data(pvq, repolist, VIZ_ID)
    if df is None:
        return nodata_graph

    # count the number of each package grouping
    df = pd.DataFrame(df["dep_age"].value_counts().reset_index())

    # graph generation
    fig = px.pie(df, names="dep_age", values="count", color_discrete_sequence=baby_blue)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Packages: %{value}<br><extra></extra>",
    )

    # add legend title
    fig["layout"]["legend_title"] = "Date Range"
    return fig
