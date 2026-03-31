import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import logging
import time
import cache_manager.cache_facade as cf
from components.visualization import VisualizationAIO
from queries.self_merge_rate_query import self_merge_rate_query as smrq
from pages.utils.graph_utils import get_graph_time_values
from pages.utils.job_utils import nodata_graph

PAGE = "contributions"
VIZ_ID = "self-merge-rate"

gc_self_merge_rate = VisualizationAIO(
    PAGE,
    VIZ_ID,
    title="Self Merge Rate",
    graph_info="""
    Tracks merged pull requests where the author and the merger are the same contributor.\n
    The top chart shows total merged PRs vs. self-merged PRs over time.\n
    The bottom chart shows the self-merge rate as a percentage of all merged PRs.\n
    CHAOSS metric definition: https://chaoss.community/kb/metric-self-merge-rates/
    """,
    controls=[
        dbc.Label(
            "Date Interval:",
            html_for=f"date-interval-{PAGE}-{VIZ_ID}",
            width="auto",
        ),
        dbc.Col(
            dbc.RadioItems(
                id=f"date-interval-{PAGE}-{VIZ_ID}",
                options=[
                    {"label": "Day", "value": "D"},
                    {"label": "Week", "value": "W"},
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
    id="self-merge-rate",
)


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def self_merge_rate_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=smrq.__name__, repolist=repolist):
        logging.warning(f"SELF MERGE RATE - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # data ready.
    start = time.perf_counter()
    logging.warning("SELF MERGE RATE - START")

    df = cf.retrieve_from_cache(
        tablename=smrq.__name__,
        repolist=repolist,
    )

    if df.empty:
        logging.warning("SELF MERGE RATE - NO DATA AVAILABLE")
        return nodata_graph

    df_plot = process_data(df, interval)
    fig = create_figure(df_plot, interval)

    logging.warning(f"SELF MERGE RATE - END - {time.perf_counter() - start}")

    return fig


def process_data(df: pd.DataFrame, interval):
    df["merged_at"] = pd.to_datetime(df["merged_at"], utc=True)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # self-merge: author == merger (with safe handling of nulls)
    df["cntrb_id"] = df["cntrb_id"].astype(str)
    df["merger_cntrb_id"] = df["merger_cntrb_id"].fillna("").astype(str)
    df["is_self_merge"] = (df["cntrb_id"] == df["merger_cntrb_id"]) & (df["merger_cntrb_id"] != "")

    # period slice for date formatting
    period_slice = 10 if interval == "W" else (4 if interval == "Y" else 7)

    # counts per period by merged_at
    merged_range = df["merged_at"].dt.to_period(interval).value_counts().sort_index()
    df_merged = merged_range.to_frame().reset_index().rename(columns={"merged_at": "Date", "count": "total_merged"})
    df_merged["Date"] = pd.to_datetime(df_merged["Date"].astype(str).str[:period_slice])

    self_merge_range = df[df["is_self_merge"]]["merged_at"].dt.to_period(interval).value_counts().sort_index()
    df_self = self_merge_range.to_frame().reset_index().rename(columns={"merged_at": "Date", "count": "self_merged"})
    df_self["Date"] = pd.to_datetime(df_self["Date"].astype(str).str[:period_slice])

    df_plot = df_merged.merge(df_self, on="Date", how="outer").fillna(0)
    df_plot["self_merged"] = df_plot["self_merged"].astype(int)
    df_plot["rate_pct"] = (df_plot["self_merged"] / df_plot["total_merged"].replace(0, float("nan")) * 100).round(1)

    if interval == "M":
        df_plot["Date_str"] = pd.to_datetime(df_plot["Date"]).dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_plot["Date_str"] = pd.to_datetime(df_plot["Date"]).dt.strftime("%Y-01-01")
    else:
        df_plot["Date_str"] = pd.to_datetime(df_plot["Date"]).dt.strftime("%Y-%m-%d")

    df_plot = df_plot.sort_values("Date").reset_index(drop=True)

    return df_plot


def create_figure(df_plot: pd.DataFrame, interval):
    x_r, x_name, hover, period = get_graph_time_values(interval)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Self Merge Rates", "Self-merge rate (%) over time"),
        vertical_spacing=0.12,
    )

    fig.add_trace(
        go.Scatter(
            name="Merged (total)",
            x=df_plot["Date_str"],
            y=df_plot["total_merged"],
            mode="lines",
            showlegend=True,
            hovertemplate="Merged (total): %{y}<br>%{x|%b %d, %Y} <extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            name="Self-merged",
            x=df_plot["Date_str"],
            y=df_plot["self_merged"],
            mode="lines",
            showlegend=True,
            hovertemplate="Self-merged: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_plot["Date_str"],
            y=df_plot["rate_pct"],
            mode="lines",
            name="Self-merge rate (%)",
            marker=dict(size=6),
            hovertemplate="%{x}<br>Rate: %{y:.1f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick=period, range=x_r)
    fig.update_yaxes(title_text="Number of PRs", row=1, col=1)
    fig.update_yaxes(title_text="Self-merge rate (%)", row=2, col=1)
    fig.update_xaxes(title_text=x_name, row=2, col=1)

    fig.update_layout(
        font=dict(size=14),
        margin_b=40,
    )

    return fig
