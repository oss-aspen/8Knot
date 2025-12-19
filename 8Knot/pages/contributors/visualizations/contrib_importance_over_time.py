from dash import html, dcc, callback
import dash
from dash import dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import polars as pl
import numpy as np
import logging
from dateutil.relativedelta import *  # type: ignore
from pages.utils.graph_utils import get_graph_time_values, baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from queries.contributors_query import contributors_query as ctq
import io
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import app
import pages.utils.preprocessing_utils as preproc_utils
import cache_manager.cache_facade as cf

PAGE = "contributors"
VIZ_ID = "lottery-factor-over-time"

gc_lottery_factor_over_time = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Lottery Factor: 6 Month Windows",
                                id=f"graph-title-{PAGE}-{VIZ_ID}",
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
                            """
                                        This analysis is also referred to as "Bus Factor". For each action type, visualizes
                                        the smallest group of contributors who account for a user-inputted percentage
                                        of the total number of contributions. By default, the threshold is set to 50%.
                                        Thus, the visualization will show the number of contributors who account for
                                        50% of all contributions made, per action type. Suppose two individuals authored
                                        50% of the commits, then the contributor prolificacy is 2. Analysis is done over
                                        a time range, and snapshots of the time range are set according to window width
                                        and step size. By default, window width and step size are set to 6 months.
                                        Thus, contributor prolificacy is calculated for each non-overlapping 6-month
                                        snapshot of the time range provided. Optionally, contributors who have 'bot' or
                                        any custom keyword(s) in their logins can be filtered out. Please note that gaps
                                        in the graph indicate that no contributions of a specific action type(s) were made
                                        during that time period.
                                        """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",  # needs to be the same as dbc.Button id
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
                                    "Window Width (Months):",
                                    html_for=f"window-width-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"window-width-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=12,
                                        step=1,
                                        value=6,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "Step Size (Months):",
                                    html_for=f"step-size-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"step-size-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=12,
                                        step=1,
                                        value=6,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Alert(
                                    children="Please ensure that 'Step Size' is less than or equal to 'Window Size'",
                                    id=f"check-alert-{PAGE}-{VIZ_ID}",
                                    dismissable=True,
                                    fade=False,
                                    is_open=False,
                                    color="warning",
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Threshold:",
                                    html_for=f"threshold-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    [
                                        dcc.Slider(
                                            id=f"threshold-{PAGE}-{VIZ_ID}",
                                            min=10,
                                            max=95,
                                            value=50,
                                            marks={i: f"{i}%" for i in range(10, 100, 5)},
                                            className="dark-slider",
                                        ),
                                    ],
                                    className="me-2",
                                    width=9,
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="bus-factor-time",
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
    Input(f"window-width-{PAGE}-{VIZ_ID}", "value"),
)
def graph_title(window_width):
    title = f"Lottery Factor: {window_width} Month Windows"
    return title


# callback for lottery-factor-over-time graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"threshold-{PAGE}-{VIZ_ID}", "value"),
        Input(f"window-width-{PAGE}-{VIZ_ID}", "value"),
        Input(f"step-size-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def create_contrib_prolificacy_over_time_graph(repolist, threshold, window_width, step_size, bot_switch):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=ctq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID} - START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=ctq.__name__,
        repolist=repolist,
    )

    df = preproc_utils.contributors_df_action_naming(df)

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    # if the step size is greater than window width raise Alert
    if step_size > window_width:
        return dash.no_update, True

    df = process_data(df, threshold, window_width, step_size)

    fig = create_figure(df, threshold, step_size)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df, threshold, window_width, step_size):
    """
    Process contributor data using Polars for initial processing, then compute lottery factors.

    The lottery factor calculation requires iterating over time windows because each window
    needs a separate groupby + pivot + cumsum operation. This is kept as a loop but uses
    Polars for the underlying data processing.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast initial processing
    pl_df = to_polars(df)

    # Convert to datetime and sort
    pl_df = pl_df.with_columns(pl.col("created_at").cast(pl.Datetime("us", "UTC")))
    pl_df = pl_df.sort("created_at")

    # Get start and end dates
    start_date = pl_df.select(pl.col("created_at").min()).item()
    end_date = pl_df.select(pl.col("created_at").max()).item()

    # Convert back to Pandas for the date range generation and loop
    # (The loop computation is inherently sequential per time window)
    df = to_pandas(pl_df)

    # === POLARS PROCESSING END ===

    # convert percent to its decimal representation
    threshold_decimal = threshold / 100

    # create bins with a size equivalent to the the step size starting from the start date up to the end date
    period_from = pd.date_range(start=start_date, end=end_date, freq=f"{step_size}m", inclusive="both")
    # store the period_from dates in a df
    df_final = period_from.to_frame(index=False, name="period_from")
    # calculate the end of each interval and store the values in a column named period_from
    df_final["period_to"] = df_final["period_from"] + pd.DateOffset(months=window_width)

    # Pre-compute lottery factors for all time windows using list comprehension
    # This is cleaner than .apply() and allows for potential future parallelization
    results = [
        cntrb_prolificacy_over_time(df, row.period_from, row.period_to, window_width, threshold_decimal)
        for row in df_final.itertuples()
    ]

    # Unpack results into columns
    if results:
        (
            df_final["Commit"],
            df_final["Issue Opened"],
            df_final["Issue Comment"],
            df_final["Issue Closed"],
            df_final["PR Opened"],
            df_final["PR Comment"],
            df_final["PR Review"],
        ) = zip(*results)

    return df_final


def create_figure(df_final, threshold, step_size):
    # create custom data to update the hovertemplate with the action type and start and end dates of a given time window in addition to the lottery factor
    # make a nested list of plural action types so that it is gramatically correct in the updated hover info eg. Commit -> Commits and PR Opened -> PRs Opened
    action_types = [
        [action_type[:2] + "s" + action_type[2:]] * len(df_final)
        if action_type == "PR Opened"
        else [action_type[:5] + "s" + action_type[5:]] * len(df_final)
        if action_type == "Issue Opened" or action_type == "Issue Closed"
        else [action_type + "s"] * len(df_final)
        for action_type in df_final.columns[2:]
    ]
    time_window = list(
        df_final["period_from"].dt.strftime("%b %d, %Y") + " - " + df_final["period_to"].dt.strftime("%b %d, %Y")
    )
    customdata = np.stack(([threshold] * len(df_final), time_window), axis=-1)

    # create plotly express line graph
    fig = go.Figure(
        [
            go.Scatter(
                name="Commit",
                x=df_final["period_from"],
                y=df_final["Commit"],
                text=action_types[0],
                customdata=customdata,
                mode="lines",
                showlegend=True,
                marker=dict(color=baby_blue[0]),
            ),
            go.Scatter(
                name="Issue Opened",
                x=df_final["period_from"],
                y=df_final["Issue Opened"],
                text=action_types[1],
                customdata=customdata,
                mode="lines",
                showlegend=True,
                marker=dict(color=baby_blue[2]),
            ),
            go.Scatter(
                name="Issue Comment",
                x=df_final["period_from"],
                y=df_final["Issue Comment"],
                text=action_types[2],
                customdata=customdata,
                mode="lines",
                showlegend=True,
                marker=dict(color=baby_blue[4]),
            ),
            go.Scatter(
                name="Issue Closed",
                x=df_final["period_from"],
                y=df_final["Issue Closed"],
                text=action_types[3],
                customdata=customdata,
                mode="lines",
                showlegend=True,
                marker=dict(color=baby_blue[6]),
            ),
            go.Scatter(
                name="PR Opened",
                x=df_final["period_from"],
                y=df_final["PR Opened"],
                text=action_types[4],
                customdata=customdata,
                mode="lines",
                showlegend=True,
                marker=dict(color=baby_blue[9]),
            ),
            go.Scatter(
                name="PR Comment",
                x=df_final["period_from"],
                y=df_final["PR Comment"],
                text=action_types[5],
                customdata=customdata,
                mode="lines",
                showlegend=True,
                marker=dict(color=baby_blue[8]),
            ),
            go.Scatter(
                name="PR Review",
                x=df_final["period_from"],
                y=df_final["PR Review"],
                text=action_types[6],
                customdata=customdata,
                mode="lines",
                showlegend=True,
                marker=dict(color=baby_blue[10]),
            ),
        ],
    )

    # define x-axis and y-axis titles and intialize first x-axis tick to start at the user-inputted start_date
    start_date = min(df_final["period_from"])

    # update xaxes to display ticks, only show ticks every other year
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        tickangle=0,
        dtick=f"M24",
        tickformat="%b %Y",
    )

    # hover template styling
    fig.update_traces(
        textposition="top right",
        hovertemplate="%{y} people contributing to<br>%{customdata[0]}% of %{text} from<br>%{customdata[1]}<br><extra></extra>",
    )

    # update xaxes to show only the year
    fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M12", tickformat="%Y")

    # layout styling
    fig.update_layout(
        xaxis_title=f"Timeline (stepsize = {step_size} months)",
        yaxis_title="Lottery Factor",
        font=dict(size=14),
        margin_b=40,
        legend_title="Action Type",
    )

    return fig


def cntrb_prolificacy_over_time(df, period_from, period_to, window_width, threshold):
    """
    Calculate lottery factor for each action type within a time window.

    Uses Polars for fast filtering and aggregation, then calculates lottery factors.
    """
    # Convert to Polars for fast filtering
    pl_df = to_polars(df)

    # Filter to time window using Polars (faster than Pandas boolean masking)
    pl_in_range = pl_df.filter((pl.col("created_at") >= period_from) & (pl.col("created_at") <= period_to))

    if pl_in_range.height == 0:
        return None, None, None, None, None, None, None

    # Count contributions per (Action, cntrb_id) using Polars groupby (2-5x faster)
    pl_counts = pl_in_range.group_by(["Action", "cntrb_id"]).agg(pl.len().alias("count"))

    # Pivot to wide format using Polars
    pl_pivot = pl_counts.pivot(
        on="Action",
        index="cntrb_id",
        values="count",
    )

    # Convert to Pandas for lottery factor calculation
    # (calc_lottery_factor uses Pandas-specific operations)
    df_count_cntrbs = to_pandas(pl_pivot).set_index("cntrb_id")

    # Calculate lottery factors for each action type
    commit = calc_lottery_factor(df_count_cntrbs, "Commit", threshold)
    issueOpened = calc_lottery_factor(df_count_cntrbs, "Issue Opened", threshold)
    issueComment = calc_lottery_factor(df_count_cntrbs, "Issue Comment", threshold)
    issueClosed = calc_lottery_factor(df_count_cntrbs, "Issue Closed", threshold)
    prOpened = calc_lottery_factor(df_count_cntrbs, "PR Opened", threshold)
    prReview = calc_lottery_factor(df_count_cntrbs, "PR Review", threshold)
    prComment = calc_lottery_factor(df_count_cntrbs, "PR Comment", threshold)

    return commit, issueOpened, issueComment, issueClosed, prOpened, prReview, prComment


def calc_lottery_factor(df, action_type, threshold):
    """Calculate the lottery factor (number of contributors needed to reach threshold).

    Uses vectorized cumsum + searchsorted instead of iterrows for 10-100x speedup.
    """
    # if the df is empty return None
    if df.empty:
        return None

    # if the specified action type is not in the dfs' cols return None
    if action_type not in df.columns:
        return None

    # drop rows where the cntrb_id is None
    mask = df.index.get_level_values("cntrb_id") == None
    df = df[~mask]

    if df.empty:
        return None

    # sort rows in df based on number of contributions from greatest to least
    df = df.sort_values(by=action_type, ascending=False)

    # calculate the threshold amount of contributions
    thresh_cntrbs = df[action_type].sum() * threshold

    # Vectorized approach: cumulative sum and binary search
    # cumsum gives running total at each position
    # searchsorted finds first position where cumsum >= threshold
    cumsum = df[action_type].cumsum()
    idx = cumsum.searchsorted(thresh_cntrbs, side="left")

    # lottery_factor is the count of contributors (1-indexed)
    # If threshold is exactly met, we need that contributor included
    lottery_factor = min(idx + 1, len(df))

    return lottery_factor
