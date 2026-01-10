from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from queries.contributors_query import contributors_query as ctq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import math
import numpy as np
import app
import pages.utils.preprocessing_utils as preproc_utils
import cache_manager.cache_facade as cf
from components.visualization import VisualizationAIO

PAGE = "chaoss"
VIZ_ID = "project-velocity"

gc_project_velocity = VisualizationAIO(
    PAGE,
    VIZ_ID,
    title="Project Velocity",
    graph_info="""
        This visualization gives a view into the development speed of a repository in\n
        relation to the other selected repositories. For more context of this visualization see\n
        https://chaoss.community/kb/metric-project-velocity/ \n
        https://www.cncf.io/blog/2017/06/05/30-highest-velocity-open-source-projects/
    """,
    controls=[
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
    ],
    class_name="dark-card",
    id="project-velocity",
)


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
    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created_at", axis=0, ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.created_at >= start_date]
    if end_date is not None:
        df = df[df.created_at <= end_date]

    # df to hold value of unique contributors for each repo
    df_cntrbs = pd.DataFrame(df.groupby("repo_name")["cntrb_id"].nunique()).rename(
        columns={"cntrb_id": "num_unique_contributors"}
    )

    # group actions and repos to get the counts of the actions by repo
    df_actions = pd.DataFrame(df.groupby("repo_name")["Action"].value_counts())
    df_actions = df_actions.rename(columns={"Action": "count"}).reset_index()

    # pivot df to reformat the actions to be columns and repo_id to be rows
    df_actions = df_actions.pivot(index="repo_name", columns="Action", values="count")

    # df_consolidated combines the actions and unique contributors and then specific columns for visualization use are added on
    df_consolidated = pd.concat([df_actions, df_cntrbs], axis=1).reset_index()

    # replace all nan to 0
    df_consolidated.fillna(value=0, inplace=True)

    # log10 of commits and contribs if values are not 0 (base-10 for intuitive decade-based reasoning)
    df_consolidated["log_num_commits"] = df_consolidated["Commit"].apply(lambda x: math.log10(x) if x != 0 else 0)
    df_consolidated["log_num_contrib"] = df_consolidated["num_unique_contributors"].apply(
        lambda x: math.log10(x) if x != 0 else 0
    )

    # column to hold the weighted values of pr and issues actions summed together
    df_consolidated["prs_issues_actions_weighted"] = (
        df_consolidated["Issue Opened"] * i_o_weight
        + df_consolidated["Issue Closed"] * i_c_weight
        + df_consolidated["PR Opened"] * pr_o_weight
        + df_consolidated["PR Merged"] * pr_m_weight
        + df_consolidated["PR Closed"] * pr_c_weight
    )

    # after weighting replace 0 with nan for log
    df_consolidated["prs_issues_actions_weighted"].replace(0, np.nan, inplace=True)

    # column for log10 value of pr and issue actions (base-10 for intuitive decade-based reasoning)
    df_consolidated["log_prs_issues_actions_weighted"] = df_consolidated["prs_issues_actions_weighted"].apply(math.log10)

    return df_consolidated


def create_figure(df: pd.DataFrame, log):
    # Use actual values instead of pre-calculated log values
    y_axis = "prs_issues_actions_weighted"
    y_title = "Weighted PR/Issue Actions"
    
    # For logarithmic scale, use actual values and set axis type to 'log'
    # This shows linear tick values (1, 10, 100, 1000) which are more intuitive
    x_axis = "Commit"
    x_title = "Commits"
    size_axis = "num_unique_contributors"
    
    if log:
        y_title = "Weighted PR/Issue Actions (log scale)"
        x_title = "Commits (log scale)"

    # graph generation
    fig = px.scatter(
        df,
        x=x_axis,
        y=y_axis,
        color="repo_name",
        size=size_axis,
        hover_data=[
            "repo_name",
            "Commit",
            "log_num_commits",
            "PR Opened",
            "Issue Opened",
            "num_unique_contributors",
            "log_num_contrib",
            "prs_issues_actions_weighted",
            "log_prs_issues_actions_weighted",
        ],
        color_discrete_sequence=baby_blue,
        log_x=log,
        log_y=log,
    )

    fig.update_traces(
        hovertemplate="Repo: %{customdata[0]}"
        + "<br>Commits: %{customdata[1]} (log10: %{customdata[2]:.2f})"
        + "<br>Total PRs: %{customdata[3]}"
        + "<br>Total Issues: %{customdata[4]}"
        + "<br>Contributors: %{customdata[5]} (log10: %{customdata[6]:.2f})"
        + "<br>Weighted Actions: %{customdata[7]:.1f} (log10: %{customdata[8]:.2f})"
        + "<br><extra></extra>",
    )

    # layout styling
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        margin_b=40,
        font=dict(size=14),
        legend_title="Repo Name",
    )

    return fig
