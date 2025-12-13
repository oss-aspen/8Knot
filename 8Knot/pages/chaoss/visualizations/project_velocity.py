from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import polars as pl
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from queries.contributors_query import contributors_query as ctq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import math
import numpy as np
import app
import pages.utils.preprocessing_utils as preproc_utils
import cache_manager.cache_facade as cf


PAGE = "chaoss"
VIZ_ID = "project-velocity"

gc_project_velocity = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Project Velocity",
                                className="card-title",
                            ),
                        ),
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
                            """This visualization gives a view into the development speed of a repository in\n
                            relation to the other selected repositories. For more context of this visualization see\n
                            https://chaoss.community/kb/metric-project-velocity/ \n
                            https://www.cncf.io/blog/2017/06/05/30-highest-velocity-open-source-projects/ """
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
                html.Hr(className="card-split"),  # Divider between graph and controls
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Issue Opened Weight:",
                                    html_for=f"issue-opened-weight-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"issue-opened-weight-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.1,
                                        value=0.3,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "Issue Closed Weight:",
                                    html_for=f"issue-closed-weight-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"issue-closed-weight-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.1,
                                        value=0.4,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "PR Open Weight:",
                                    html_for=f"pr-open-weight-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"pr-open-weight-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.1,
                                        value=0.5,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "PR Merged Weight:",
                                    html_for=f"pr-merged-weight-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"pr-merged-weight-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.1,
                                        value=0.7,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "PR Closed Weight:",
                                    html_for=f"pr-closed-weight-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"pr-closed-weight-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.1,
                                        value=0.2,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "Y-axis:",
                                    html_for=f"graph-view-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id=f"graph-view-{PAGE}-{VIZ_ID}",
                                        options=[
                                            {"label": "Non-log", "value": False},
                                            {"label": "Log", "value": True},
                                        ],
                                        value=False,
                                        inline=True,
                                        className="custom-radio-buttons",
                                    ),
                                    className="me-2",
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.DatePickerRange(
                                        id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                        min_date_allowed=dt.date(2005, 1, 1),
                                        max_date_allowed=dt.date.today(),
                                        initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                        clearable=True,
                                        className="dark-date-picker",
                                    ),
                                    width=7,
                                ),
                            ],
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="project-velocity",
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


# callback for Project Velocity graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
        Input(f"issue-opened-weight-{PAGE}-{VIZ_ID}", "value"),
        Input(f"issue-closed-weight-{PAGE}-{VIZ_ID}", "value"),
        Input(f"pr-open-weight-{PAGE}-{VIZ_ID}", "value"),
        Input(f"pr-merged-weight-{PAGE}-{VIZ_ID}", "value"),
        Input(f"pr-closed-weight-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def project_velocity_graph(
    repolist,
    log,
    i_o_weight,
    i_c_weight,
    pr_o_weight,
    pr_m_weight,
    pr_c_weight,
    start_date,
    end_date,
    bot_switch,
):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=ctq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=ctq.__name__,
        repolist=repolist,
    )

    df = preproc_utils.contributors_df_action_naming(df)

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # function for all data pre processing
    df = process_data(
        df,
        start_date,
        end_date,
        i_o_weight,
        i_c_weight,
        pr_o_weight,
        pr_m_weight,
        pr_c_weight,
    )

    fig = create_figure(df, log)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(
    df: pd.DataFrame,
    start_date,
    end_date,
    i_o_weight,
    i_c_weight,
    pr_o_weight,
    pr_m_weight,
    pr_c_weight,
):
    """
    Process project velocity data using Polars for performance.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast processing
    pl_df = to_polars(df)

    # Convert to datetime and sort
    pl_df = pl_df.with_columns(pl.col("created_at").cast(pl.Datetime("us", "UTC")))
    pl_df = pl_df.sort("created_at")

    # Filter by date range
    if start_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") >= start_date)
    if end_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") <= end_date)

    # Count unique contributors per repo
    pl_cntrbs = pl_df.group_by("repo_name").agg(pl.col("cntrb_id").n_unique().alias("num_unique_contributors"))

    # Count actions per repo
    pl_actions = (
        pl_df.group_by(["repo_name", "Action"])
        .agg(pl.len().alias("count"))
        .pivot(on="Action", index="repo_name", values="count")
    )

    # Join contributors and actions
    pl_consolidated = pl_actions.join(pl_cntrbs, on="repo_name", how="left")

    # Fill nulls with 0
    pl_consolidated = pl_consolidated.fill_null(0)

    # Ensure all required columns exist with 0 default
    for col in ["Commit", "Issue Opened", "Issue Closed", "PR Opened", "PR Merged", "PR Closed"]:
        if col not in pl_consolidated.columns:
            pl_consolidated = pl_consolidated.with_columns(pl.lit(0).alias(col))

    # Calculate log values using Polars expressions
    pl_consolidated = pl_consolidated.with_columns(
        [
            pl.when(pl.col("Commit") != 0).then(pl.col("Commit").log()).otherwise(0).alias("log_num_commits"),
            pl.when(pl.col("num_unique_contributors") != 0)
            .then(pl.col("num_unique_contributors").log())
            .otherwise(0)
            .alias("log_num_contrib"),
        ]
    )

    # Calculate weighted PR/Issue actions
    pl_consolidated = pl_consolidated.with_columns(
        (
            pl.col("Issue Opened") * i_o_weight
            + pl.col("Issue Closed") * i_c_weight
            + pl.col("PR Opened") * pr_o_weight
            + pl.col("PR Merged") * pr_m_weight
            + pl.col("PR Closed") * pr_c_weight
        ).alias("prs_issues_actions_weighted")
    )

    # Replace 0 with null for log, then calculate log
    pl_consolidated = pl_consolidated.with_columns(
        pl.when(pl.col("prs_issues_actions_weighted") == 0)
        .then(None)
        .otherwise(pl.col("prs_issues_actions_weighted"))
        .alias("prs_issues_actions_weighted")
    )
    pl_consolidated = pl_consolidated.with_columns(
        pl.col("prs_issues_actions_weighted").log().alias("log_prs_issues_actions_weighted")
    )

    # === POLARS PROCESSING END ===

    # Convert to Pandas for visualization
    return to_pandas(pl_consolidated)


def create_figure(df: pd.DataFrame, log):
    y_axis = "prs_issues_actions_weighted"
    y_title = "Weighted PR/Issue Actions"
    if log:
        y_axis = "log_prs_issues_actions_weighted"
        y_title = "Log of Weighted PR/Issue Actions"

    # graph generation
    fig = px.scatter(
        df,
        x="log_num_commits",
        y=y_axis,
        color="repo_name",
        size="log_num_contrib",
        hover_data=[
            "repo_name",
            "Commit",
            "PR Opened",
            "Issue Opened",
            "num_unique_contributors",
        ],
        color_discrete_sequence=baby_blue,
    )

    fig.update_traces(
        hovertemplate="Repo: %{customdata[0]} <br>Commits: %{customdata[1]} <br>Total PRs: %{customdata[2]}"
        + "<br>Total Issues: %{customdata[3]} <br>Total Contributors: %{customdata[4]}<br><extra></extra>",
    )

    # layout styling
    fig.update_layout(
        xaxis_title="Logarithmic Commits",
        yaxis_title=y_title,
        margin_b=40,
        font=dict(size=14),
        legend_title="Repo Name",
    )

    return fig
