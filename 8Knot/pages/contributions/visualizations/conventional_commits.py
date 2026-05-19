import logging
import re
import time

import cache_manager.cache_facade as cf
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from components.visualization import VisualizationAIO
from dash import callback
from dash.dependencies import Input, Output
from pages.utils.graph_utils import baby_blue, get_graph_time_values
from pages.utils.job_utils import nodata_graph
from queries.commits_query import commits_query as cmq

PAGE = "contributions"
VIZ_ID = "conventional-commits"

CONVENTIONAL_COMMIT_RE = re.compile(r"^(?P<commit_type>[A-Za-z][A-Za-z0-9-]*)(?:\([^)]*\))?!?:")
CONVENTIONAL_TYPE_ORDER = [
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
    "other",
]

gc_conventional_commits = VisualizationAIO(
    PAGE,
    VIZ_ID,
    title="Conventional Commits Breakdown",
    graph_info="""
    Visualizes commits by Conventional Commit type over a user-selected time window.\n
    Commits that do not match the Conventional Commit prefix format are counted as "other".
    """,
    controls=[
        dbc.Label(
            "Date Interval:",
            html_for=f"date-interval-{PAGE}-{VIZ_ID}",
            width={"size": "auto"},
        ),
        dbc.Col(
            dbc.RadioItems(
                id=f"date-interval-{PAGE}-{VIZ_ID}",
                options=[
                    {
                        "label": "Day",
                        "value": "D",
                    },
                    {
                        "label": "Week",
                        "value": "W",
                    },
                    {"label": "Month", "value": "M"},
                    {"label": "Year", "value": "Y"},
                ],
                value="M",
                inline=True,
                className="custom-radio-buttons",
            ),
            className="me-2",
            width=4,
        ),
    ],
    class_name="dark-card",
    id="conventional-commits",
)


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def conventional_commits_graph(repolist, interval):
    while not_cached := cf.get_uncached(func_name=cmq.__name__, repolist=repolist):
        logging.warning("CONVENTIONAL_COMMITS_VIZ - WAITING ON DATA")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning("CONVENTIONAL_COMMITS_VIZ - START")

    df = cf.retrieve_from_cache(
        tablename=cmq.__name__,
        repolist=repolist,
    )

    if df.empty:
        logging.warning("CONVENTIONAL_COMMITS_VIZ - NO DATA AVAILABLE")
        return nodata_graph

    df_created = process_data(df, interval)
    if df_created.empty:
        logging.warning("CONVENTIONAL_COMMITS_VIZ - NO COMMIT MESSAGES AVAILABLE")
        return nodata_graph

    fig = create_figure(df_created, interval)

    logging.warning(f"CONVENTIONAL_COMMITS_VIZ - END - {time.perf_counter() - start}")
    return fig


def extract_commit_type(commit_message):
    if pd.isna(commit_message):
        return "other"

    subject = str(commit_message).splitlines()[0].strip()
    match = CONVENTIONAL_COMMIT_RE.match(subject)
    if not match:
        return "other"

    return match.group("commit_type").lower()


def process_data(df: pd.DataFrame, interval):
    df = df.copy()
    if "commit_message" not in df.columns:
        df["commit_message"] = None

    df["author_date"] = pd.to_datetime(df["author_date"], utc=True)
    df["commit_type"] = df["commit_message"].apply(extract_commit_type)

    period_slice = None
    if interval == "W":
        period_slice = 10

    df_created = (
        df.groupby([df.author_date.dt.to_period(interval), "commit_type"])["commit_hash"]
        .nunique()
        .reset_index()
        .rename(columns={"author_date": "Date", "commit_hash": "commits"})
    )
    df_created["Date"] = pd.to_datetime(df_created["Date"].astype(str).str[:period_slice])

    return df_created.sort_values(["Date", "commit_type"])


def create_figure(df_created: pd.DataFrame, interval):
    x_r, x_name, hover, period = get_graph_time_values(interval)

    fig = px.bar(
        df_created,
        x="Date",
        y="commits",
        color="commit_type",
        range_x=x_r,
        labels={
            "Date": x_name,
            "commits": "Commits",
            "commit_type": "Commit Type",
        },
        category_orders={"commit_type": CONVENTIONAL_TYPE_ORDER},
        color_discrete_sequence=baby_blue,
    )
    fig.update_traces(hovertemplate=hover + "<br>Type: %{fullData.name}<br>Commits: %{y}<br>")
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        rangeslider_yaxis_rangemode="match",
        range=x_r,
    )
    fig.update_layout(
        barmode="stack",
        xaxis_title=x_name,
        yaxis_title="Number of Commits",
        margin_b=40,
        margin_r=20,
        font=dict(size=14),
        legend_title_text="Commit Type",
    )

    return fig
