import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import logging
import time

import cache_manager.cache_facade as cf
import app  # pylint: disable=unused-import
from components.visualization import VisualizationAIO
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.job_utils import nodata_graph
from queries.self_merge_rate_query import self_merge_rate_query as smrq

PAGE = "contributions"
VIZ_ID = "self-merge-rate"

gc_self_merge_rate = VisualizationAIO(
    PAGE,
    VIZ_ID,
    title="Self Merge Rate",
    graph_info="""
    Shows PRs merged over time and the PRs merged by the same contributor as the
    author (self-merge).\n
    See https://chaoss.community/kb/metric-self-merge-rates/
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


def _bucket_merged_prs(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Aggregate merged and self-merged counts by time bucket; add rate (%)."""
    work = df.copy()
    work["merged_at"] = pd.to_datetime(work["merged_at"], utc=True)
    work["cntrb_id"] = work["cntrb_id"].astype(str)
    work["merger_cntrb_id"] = work["merger_cntrb_id"].fillna("").astype(str)
    work["is_self_merge"] = (work["cntrb_id"] == work["merger_cntrb_id"]) & (work["merger_cntrb_id"] != "")

    period_slice = 10 if interval == "W" else None

    merged_range = work["merged_at"].dt.to_period(interval).value_counts().sort_index()
    df_merged = merged_range.to_frame().reset_index().rename(columns={"merged_at": "Date", "count": "total_merged"})
    df_merged["Date"] = pd.to_datetime(df_merged["Date"].astype(str).str[:period_slice])

    self_merge_range = work.loc[work["is_self_merge"], "merged_at"].dt.to_period(interval).value_counts().sort_index()
    df_self = self_merge_range.to_frame().reset_index().rename(columns={"merged_at": "Date", "count": "self_merged"})
    df_self["Date"] = pd.to_datetime(df_self["Date"].astype(str).str[:period_slice])

    df_plot = df_merged.merge(df_self, on="Date", how="outer").fillna(0)
    df_plot["self_merged"] = df_plot["self_merged"].astype(int)
    df_plot["total_merged"] = df_plot["total_merged"].astype(int)
    df_plot["rate_pct"] = (df_plot["self_merged"] / df_plot["total_merged"].replace(0, float("nan")) * 100).round(1)

    if interval == "M":
        df_plot["Date_str"] = pd.to_datetime(df_plot["Date"]).dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_plot["Date_str"] = pd.to_datetime(df_plot["Date"]).dt.strftime("%Y-01-01")
    else:
        df_plot["Date_str"] = pd.to_datetime(df_plot["Date"]).dt.strftime("%Y-%m-%d")

    return df_plot.sort_values("Date").reset_index(drop=True)


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def self_merge_rate_graph(repolist, interval):
    while not_cached := cf.get_uncached(func_name=smrq.__name__, repolist=repolist):
        logging.warning("SELF MERGE RATE - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning("SELF MERGE RATE - START")

    df = cf.retrieve_from_cache(
        tablename=smrq.__name__,
        repolist=repolist,
    )

    if df.empty:
        logging.warning("SELF MERGE RATE - NO DATA AVAILABLE")
        return nodata_graph

    df_plot = _bucket_merged_prs(df, interval)
    if df_plot.empty:
        logging.warning("SELF MERGE RATE - NO BUCKETS AFTER PROCESSING")
        return nodata_graph

    x_r, x_name, hover, period = get_graph_time_values(interval)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Merged pull requests", "Self-merge rate (%)"),
        row_heights=[0.52, 0.48],
    )

    fig.add_trace(
        go.Scatter(
            name="Merged (total)",
            x=df_plot["Date_str"],
            y=df_plot["total_merged"],
            mode="lines",
            line=dict(color=baby_blue[0]),
            hovertemplate=hover + "<br>Merged (total): %{y}<extra></extra>",
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
            line=dict(color=baby_blue[6]),
            hovertemplate=hover + "<br>Self-merged: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            name="Self-merge rate (%)",
            x=df_plot["Date_str"],
            y=df_plot["rate_pct"],
            mode="lines",
            line=dict(color=baby_blue[4]),
            hovertemplate=hover + "<br>Rate: %{y:.1f}%<extra></extra>",
            connectgaps=False,
        ),
        row=2,
        col=1,
    )

    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        range=x_r,
        title_text=x_name,
        row=2,
        col=1,
    )
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        range=x_r,
        row=1,
        col=1,
    )
    fig.update_yaxes(title_text="Number of PRs", row=1, col=1)
    fig.update_yaxes(title_text="Self-merge rate (%)", row=2, col=1)

    fig.update_layout(
        height=640,
        font=dict(size=14),
        margin=dict(t=48, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        showlegend=True,
    )

    logging.warning(f"SELF MERGE RATE - END - {time.perf_counter() - start}")

    return fig
