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
from pages.utils.job_utils import nodata_graph
import time
import app
from queries.contributors_query import contributors_query as ctq
import pages.utils.preprocessing_utils as preproc_utils
import cache_manager.cache_facade as cf

PAGE = "contributors"
VIZ_ID = "active-drifting-contributors"

gc_active_drifting_contributors = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Contributor Growth by Engagement",
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
                            Visualizes growth of contributor population, including sub-populations\n
                            in consideration of how recently a contributor has contributed.\n
                            Please see definitions of 'Contributor Recency' on Info page.
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
                                    "Months Until Drifting:",
                                    html_for=f"drifting-months-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"drifting-months-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=120,
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
                                    "Months Until Away:",
                                    html_for=f"away-months-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"away-months-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=120,
                                        step=1,
                                        value=12,
                                        size="sm",
                                        style={"width": "80px"},
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Alert(
                                    children="Please ensure that 'Months Until Drifting' is less than 'Months Until Away'",
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
                                    "Date Interval:",
                                    html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-interval-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "Trend", "value": "D"},
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
                                            inline=True,
                                            className="custom-radio-buttons",
                                        ),
                                    ]
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
    id="engagement-growth",
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


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
        Input(f"drifting-months-{PAGE}-{VIZ_ID}", "value"),
        Input(f"away-months-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def active_drifting_contributors_graph(repolist, interval, drift_interval, away_interval, bot_switch):
    # conditional for the intervals to be valid options
    if drift_interval is None or away_interval is None:
        return dash.no_update, dash.no_update

    if drift_interval > away_interval:
        return dash.no_update, True

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
        logging.warning("ACTIVE_DRIFTING_CONTRIBUTOR_GROWTH - NO DATA AVAILABLE")
        return nodata_graph, False

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # function for all data pre processing
    df_status = process_data(df, interval, drift_interval, away_interval)

    fig = create_figure(df_status, interval)

    logging.warning(f"ACTIVE_DRIFTING_CONTRIBUTOR_GROWTH_VIZ - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, interval, drift_interval, away_interval):
    """
    Process contributor data using Polars for performance, returning Pandas for visualization.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast initial processing
    pl_df = to_polars(df)

    # Convert to datetime and sort
    pl_df = pl_df.with_columns(pl.col("created_at").cast(pl.Datetime("us", "UTC")))
    pl_df = pl_df.sort("created_at")

    # Get date range
    earliest = pl_df.select(pl.col("created_at").min()).item()
    latest = pl_df.select(pl.col("created_at").max()).item()

    # Convert to Pandas for date range generation and loop processing
    df = to_pandas(pl_df)

    # === POLARS PROCESSING END ===

    # Generate date range
    dates = pd.date_range(start=earliest, end=latest, freq=interval, inclusive="both")
    df_status = dates.to_frame(index=False, name="Date")

    # Use list comprehension instead of .apply() (cleaner, same performance)
    results = [get_active_drifting_away_up_to(df, date, drift_interval, away_interval) for date in df_status["Date"]]

    if results:
        df_status["Active"], df_status["Drifting"], df_status["Away"] = zip(*results)

    # Format dates for graph generation
    if interval == "M":
        df_status["Date"] = df_status["Date"].dt.strftime("%Y-%m")
    elif interval == "Y":
        df_status["Date"] = df_status["Date"].dt.year

    return df_status


def create_figure(df_status: pd.DataFrame, interval):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # making a line graph if the bin-size is small enough.
    if interval == "D":
        fig = go.Figure(
            [
                go.Scatter(
                    name="Active",
                    x=df_status["Date"],
                    y=df_status["Active"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors Active: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=baby_blue[6]),
                ),
                go.Scatter(
                    name="Drifting",
                    x=df_status["Date"],
                    y=df_status["Drifting"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors Drifting: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=baby_blue[2]),
                ),
                go.Scatter(
                    name="Away",
                    x=df_status["Date"],
                    y=df_status["Away"],
                    mode="lines",
                    showlegend=True,
                    hovertemplate="Contributors Away: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
                    marker=dict(color=baby_blue[0]),
                ),
            ]
        )
    else:
        fig = px.bar(
            df_status,
            x="Date",
            y=["Active", "Drifting", "Away"],
            color_discrete_sequence=[baby_blue[6], baby_blue[2], baby_blue[0]],
        )

        # edit hover values
        fig.update_traces(hovertemplate=hover + "<br>Contributors: %{y}<br>" + "<extra></extra>")

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Contributors",
        legend_title="Type",
        font=dict(size=14),
    )

    return fig


def get_active_drifting_away_up_to(df, date, drift_interval, away_interval):
    """
    Calculate active, drifting, and away contributors up to a given date.

    Uses Polars for fast filtering operations (2-5x faster than Pandas).
    """
    # Convert to Polars for fast filtering
    pl_df = to_polars(df)

    # Filter to contributions up to date, keep last per contributor
    pl_lim = (
        pl_df.filter(pl.col("created_at") <= date)
        .sort("created_at", descending=True)
        .unique(subset=["cntrb_id"], keep="first")
    )

    if pl_lim.height == 0:
        return [0, 0, 0]

    # Calculate time thresholds
    drift_mos = date - relativedelta(months=+drift_interval)
    away_mos = date - relativedelta(months=+away_interval)

    # Count contributors in each category using Polars (faster than Pandas boolean indexing)
    numTotal = pl_lim.height

    # Active: last contribution >= drift threshold
    numActive = pl_lim.filter(pl.col("created_at") >= drift_mos).height

    # Drifting: last contribution between away and drift thresholds
    numDrifting = pl_lim.filter((pl.col("created_at") > away_mos) & (pl.col("created_at") < drift_mos)).height

    # Away: the rest
    numAway = numTotal - (numActive + numDrifting)

    return [numActive, numDrifting, numAway]
