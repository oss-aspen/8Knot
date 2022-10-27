from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values

from pages.utils.job_utils import handle_job_state, nodata_graph
from queries.issues_query import issues_query as iq
from app import jm

import time

# callback for issues over time graph
@callback(
    Output("issues-over-time", "figure"),
    Output("issues-over-time-timer", "n_intervals"),
    [
        Input("repo-choices", "data"),
        Input("issues-over-time-timer", "n_intervals"),
        Input("issue-time-interval", "value"),
    ],
)
def issues_over_time_graph(repolist, timer_pings, interval):
    logging.debug("IOT - PONG")

    # start timer
    start = time.perf_counter()
    
    ready, results, graph_update, interval_update = handle_job_state(jm, iq, repolist)
    if not ready:
        return graph_update, interval_update

    logging.debug("ISSUES_OVER_TIME_VIZ - START")

    # default time values for figure
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # process raw data into plotable format
    df = process_data(results, period)

    # no data might be available.
    if df is None:
        logging.debug("ISSUES_OVER_TIME_VIZ - NO DATA AVAILABLE")
        return nodata_graph, dash.no_update

    # create figure from processed data
    fig = create_figure(df, x_r, x_name, hover, interval)

    logging.debug(f"ISSUES_OVER_TIME_VIZ - END - {time.perf_counter() - start}")
    return fig, dash.no_update

    
def process_data(results, period):
    # load data into dataframe
    df = pd.DataFrame(results).reset_index()

    # check that there are datapoints to render.
    if df.shape[0] == 0:
        return None

    # from POSIX timestamp to datetime, sort in ascending order
    df["created"] = pd.to_datetime(df["created"], unit="s").sort_values()
    df["closed"] = pd.to_datetime(df["closed"], unit="s").sort_values()

    # timestamps of issues being created 
    df_created = df["created"]
    # group data by period and count instances, sort by time from earlier to later
    df_created_period = pd.to_datetime(df_created["created"]).dt.to_period(period).value_counts().sort_index()
    # because index is PeriodIndex we can convert to a series and then to a string easily
    df_created_period.index = pd.PeriodIndex(df_created_period.index).to_series().astype(str)
    # name the time index and the counts index
    df_created_period = df_created_period.rename_axis("period").reset_index(name="counts")
    # set created event
    df_created_period["event_type"] = "created"

    # timestamps of when issues being closed
    df_closed = df[df["closed"].notna()]["closed"]
    # group data by period and count instances, sort by time from earlier to later
    df_closed_period = pd.to_datetime(df_closed["closed"]).dt.to_period(period).value_counts().sort_index()
    # because index is PeriodIndex we can convert to a series and then to a string easily
    df_closed_period.index = pd.PeriodIndex(df_closed_period.index).to_series().astype(str)
    # name the time index and the counts index
    df_closed_period = df_closed_period.rename_axis("period").reset_index(name="counts")
    # set created event
    df_closed_period["event_type"] = "closed"

    df_concat = pd.concat([df_created_period, df_closed_period], ignore_index=True, axis=0)

    return df_concat

def create_figure(df: pd.DataFrame, x_r, x_name, hover, interval):
    fig = go.Figure()
    fig.add_bar(
        x=df[df["event_type"] == "created"]["created"],
        y=df[df["event_type"] == "created"]["counts"],
        name="created",
        opacity=0.6,
        hovertemplate=hover + "<br>Created: %{y}<br>" + "<extra></extra>"
    )
    fig.add_bar(
        x=df[df["event_type"] == "closed"]["closed"],
        y=df[df["event_type"] == "closed"]["counts"],
        name="closed",
        opacity=0.6,
        hovertemplate=hover + "<br>Closed: %{y}<br>" + "<extra></extra>"
    )
    fig.update_traces(xbins_size=interval)
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="instant",
        dtick=interval,
        rangeslider_yaxis_rangemode="match",
        range=x_r,
    )
    fig.update_layout(
        xaxis_title=x_name,
        yaxis_title="Number of Issues",
        bargroupgap=0.1,
        margin_b=40,
    )

    #fig = px.bar(data_frame=df, x="period", y="counts", barmode="group", color="event_type")
    return fig
    