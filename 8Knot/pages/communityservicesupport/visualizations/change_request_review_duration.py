from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.prs_query import prs_query as prs
from queries.change_request_review_query import change_request_review_query as crr
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import math
import numpy as np


PAGE = "communityservicesupport"
VIZ_ID = "change-request-review-duration"

gc_change_request_review_duration = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Change Request Review Duration",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """The Change Request Review Duration metric measures the time from when a submitter has submitted a change within a review cycle until it is reviewed.\n
                            This metric measures one review, however, there may be multiple reviews within a Review Cycle Duration within a Change Request and this measures time of each review.\n
                            The time waiting for a review is zero if the change request is merged without any requested revisions or clarification. For more context of this visualization see \n
                            https://chaoss.community/kb/metric-change-request-review-duration/ \n """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",  # needs to be the same as dbc.Button id
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
                                dbc.Col(
                                    dcc.DatePickerRange(
                                        id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                        min_date_allowed=dt.date(2005, 1, 1),
                                        max_date_allowed=dt.date.today(),
                                        initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                        clearable=True,
                                    ),
                                    width="auto",
                                ),
                            ],
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-interval-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
                                            inline=True,
                                        ),
                                    ]
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

# callback for Change Request Review Duration graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    # Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"), USE WITH ADDITIONAL PARAMETERS
    # if additional output is added, change returns accordingly
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
        # add additional inputs here
    ],
    background=True,
)
def change_request_review_duration_graph(repolist, interval, start_date, end_date):
    # Fetch and process the data
    cache = cm()
    df = cache.grabm(func=crr, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=crr, repos=repolist)
    
    # data ready.
    start = time.perf_counter()
    logging.warning("CHANGE REQUEST REVIEW DURATION - START")
    
    # Test the dataframe has data
    if df is None:
        logging.warning(f"DataFrame is None for Repos: {repolist}")
        return go.Figure().update_layout(title="No data available")
    if df.empty:
        logging.warning(f"DataFrame is empty for Repos: {repolist}")
        return go.Figure().update_layout(title="No data available")
    
    # Process the data
    processed_df = process_data(df, interval, start_date, end_date)

    fig = create_figure(processed_df, interval)
    
    logging.warning(f"CHANGE_REQUEST_REVIEW_DURATION_VIZ - END - {time.perf_counter() - start}")

    return fig

def process_data(df: pd.DataFrame, interval, start_date, end_date):
    # convert timestamps to dates and handle UUID conversion if necessary
    df["pr_created_at"] = pd.to_datetime(df["pr_created_at"], utc=True)
    df["pr_closed_at"] = pd.to_datetime(df["pr_closed_at"], utc=True)
    df["pr_merged_at"] = pd.to_datetime(df["pr_merged_at"], utc=True)
    
    # Calculate 'days_to_merge'
    df["days_to_merge"] = (df["pr_merged_at"] - df["pr_created_at"]).dt.days
    
    # Handle missing or invalid data
    df = df.dropna(subset=['pr_created_at'])
    df = df[df['days_to_merge'].notna() & (df['days_to_merge'] >= 0)]
    
    # Convert start_date and end_date to datetime if they are not None
    if start_date is not None:
        start_date = pd.to_datetime(start_date, utc=True)
        df = df[df["pr_created_at"] >= start_date]

    if end_date is not None:
        end_date = pd.to_datetime(end_date, utc=True)
        df = df[df["pr_created_at"] <= end_date]

    # Sort values and group by the specified interval
    df = df.sort_values(by="pr_created_at", ascending=True)
    if interval == 'M':
        df['period'] = df['pr_created_at'].dt.to_period('M')
    elif interval == 'Y':
        df['period'] = df['pr_created_at'].dt.to_period('Y')
    else:
        raise ValueError("Invalid interval selected")

    stats_df = df.groupby('period').agg({
        'days_to_first_response': 'mean',
        'days_to_last_response': 'mean',
        'days_to_close': 'mean',
        'days_to_merge': 'mean',
    }).reset_index()
    
    return stats_df

def create_figure(df, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)
    
    # Create the figure
    fig = go.Figure()
    metrics = ['days_to_first_response', 'days_to_last_response', 'days_to_close', 'days_to_merge']
    bar_names = ['Mean Days to First Response', 'Mean Days to Last Response', 'Mean Days to Close', 'Mean Days to Merge']

    for col, bar_name in zip(metrics, bar_names):
        fig.add_trace(go.Bar(
            x=df['period'].astype(str),  # Convert period to string for plotting
            y=df[col],
            name=bar_name
        ))

    # Customize layout
    fig.update_layout(
        xaxis_title='Time Period',
        yaxis_title='Days',
        barmode='group',
        legend_title='Legend'
    )

    # Return the figure
    return fig
