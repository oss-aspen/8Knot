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
        # add additional inputs here
    ],
    background=True,
)
def change_request_review_duration_graph(repolist, interval):
    # Fetch and process the data
    cache = cm()
    df = cache.grabm(func=crr, repos=repolist)
    if df is None or df.empty:
        return go.Figure().update_layout(title="No data available")

    processed_df = process_data(df)
    stats_df = calculate_statistics(processed_df, interval)

    # Create the figure
    fig = go.Figure()
    bar_names = ['Mean Days to First Response', 'Mean Days to Last Response', 'Mean Days to Close', 'Mean Days to Accepted']

    for col, bar_name in zip(['first_response_days', 'last_response_days', 'close_days', 'accept_days'], bar_names):
        fig.add_trace(go.Bar(
            x=stats_df['period'],
            y=stats_df[col],
            name=bar_name
        ))

    # Customize layout
    fig.update_layout(
        title='Mean Response Times for Pull Requests',
        xaxis_title='Time Period',
        yaxis_title='Days',
        barmode='group',
        legend_title='Metrics'
    )

    return fig

def process_data(df):
    df['first_response_days'] = (df['first_response_timestamp'] - df['pr_created_at']).dt.days
    df['last_response_days'] = (df['last_response_timestamp'] - df['pr_created_at']).dt.days
    df['close_days'] = (df['pr_closed_at'] - df['pr_created_at']).dt.days
    df['accept_days'] = (df['pr_merged_at'] - df['pr_created_at']).dt.days
    return df

"""
def process_data(df: pd.DataFrame):
    # Convert to datetime objects rather than strings
    df["pr_created_at"] = pd.to_datetime(df["pr_created_at"], utc=True)
    df["pr_merged_at"] = pd.to_datetime(df["pr_merged_at"], utc=True)
    df["pr_closed_at"] = pd.to_datetime(df["pr_closed_at"], utc=True)

    # Calculate the required statistics
    df['first_response_days'] = (df['first_response_timestamp'] - df['pr_created_at']).dt.days
    df['last_response_days'] = (df['last_response_timestamp'] - df['pr_created_at']).dt.days
    df['close_days'] = (df['pr_closed_at'] - df['pr_created_at']).dt.days
    df['accept_days'] = (df['pr_merged_at'] - df['pr_created_at']).dt.days
    
    # Group by Year/Month
    df['year_month'] = df['pr_created_at'].dt.to_period('M')
    grouped = df.groupby('year_month')
    
    # Calculate mean for each group
    stats = grouped.agg({
        'first_response_days': 'mean',
        'last_response_days': 'mean',
        'close_days': 'mean',
        'accept_days': 'mean'
    }).reset_index()
    
    return stats
"""

def create_figure(stats_df, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)
    
    # Create the figure
    fig = px.bar(
            stats_df,
            x=stats_df['year_month'],
            y=stats_df['first_response_days', 'last_response_days', 'close_days', 'accept_days'],
            color_discrete_sequence=[color_seq[1], color_seq[5], color_seq[2], color_seq[0]],
        )

    # edit hover values
    fig.update_traces(hovertemplate=hover + "<br>PRs: %{y}<br>" + "<extra></extra>")

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Pull Requests",
        legend_title="Type",
        font=dict(size=14),
    )
    
    # Customize layout with the legend
    fig.update_layout(
        title='Mean Response Times for Pull Requests All Closed',
        xaxis_title='Year/Month',
        yaxis_title='Days to Close',
        legend_title='Metrics',
        barmode='group',
        legend=dict(orientation="h")  # Horizontal legend below the chart
    )

    # Return the figure
    return fig

def calculate_statistics(df, interval):
    if interval == 'M':
        df['period'] = df['pr_created_at'].dt.to_period('M')
    else:
        df['period'] = df['pr_created_at'].dt.to_period('Y')

    stats = df.groupby('period').agg({
        'first_response_days': 'mean',
        'last_response_days': 'mean',
        'close_days': 'mean',
        'accept_days': 'mean'
    }).reset_index()

    return stats

"""
def calculate_statistics(df):
    # Example calculations, you will need to adjust based on your actual DataFrame structure
    df['first_response_days'] = (df['first_response_timestamp'] - df['pr_created_at']).dt.days
    df['last_response_days'] = (df['last_response_timestamp'] - df['pr_created_at']).dt.days
    df['close_days'] = (df['pr_closed_at'] - df['pr_created_at']).dt.days
    df['accept_days'] = (df['pr_merged_at'] - df['pr_created_at']).dt.days
    
    # Group by Year/Month
    df['year_month'] = df['pr_created_at'].dt.to_period('M')
    grouped = df.groupby('year_month')
    
    # Calculate mean for each group
    stats = grouped.agg({
        'first_response_days': 'mean',
        'last_response_days': 'mean',
        'close_days': 'mean',
        'accept_days': 'mean'
    }).reset_index()
    
    return stats
"""