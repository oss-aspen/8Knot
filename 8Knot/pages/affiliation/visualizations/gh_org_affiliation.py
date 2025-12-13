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
from pages.utils.graph_utils import baby_blue
from pages.utils.polars_utils import to_polars, to_pandas
from queries.affiliation_query import affiliation_query as aq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
from rapidfuzz import fuzz
import app
import cache_manager.cache_facade as cf

PAGE = "affiliation"
VIZ_ID = "gh-org-affiliation"

gc_gh_org_affiliation = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Organization Affiliation by GitHub Account Info",
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
                            Visualizes GitHub account institution affiliation.\n
                            Many individuals don't report an affiliated institution, but\n
                            this count may be considered an absolute lower-bound on affiliation.
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
                                    "Contributions Required:",
                                    html_for=f"contributions-required-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"contributions-required-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=50,
                                        step=1,
                                        value=5,
                                        size="sm",
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
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
                            align="center",
                            justify="start",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        ),
    ],
    className="dark-card",
    id="gh-org-affiliation",
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


# callback for Organization Affiliation by Github Account Info graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"contributions-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def gh_org_affiliation_graph(repolist, num, start_date, end_date, bot_switch):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=aq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=aq.__name__,
        repolist=repolist,
    )
    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, num, start_date, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, num, start_date, end_date):
    """
    Process GitHub organization affiliation data using Polars for initial processing.

    Follows the "Polars Core, Pandas Edge" architecture.
    Note: Fuzzy matching still uses Pandas due to external library requirements.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast initial filtering
    pl_df = to_polars(df)

    # Convert to datetime and sort
    pl_df = pl_df.with_columns(pl.col("created_at").cast(pl.Datetime("us", "UTC")))
    pl_df = pl_df.sort("created_at")

    # Filter by date range
    if start_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") >= start_date)
    if end_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") <= end_date)

    # Count company affiliations using Polars (faster than value_counts)
    pl_counts = (
        pl_df.group_by("cntrb_company")
        .agg(pl.len().alias("contribution_count"))
        .with_columns(pl.col("cntrb_company").cast(pl.Utf8).alias("company_name"))
    )

    # Convert to Pandas for fuzzy matching (requires external library)
    df = to_pandas(pl_counts)

    # === POLARS PROCESSING END ===

    # Fuzzy matching (keeping in Pandas due to rapidfuzz requirements)
    df["match"] = df.apply(lambda row: fuzzy_match(df, row["company_name"]), axis=1)

    # Apply fuzzy match results
    for x in range(0, len(df)):
        matches = df.iloc[x]["match"]
        for y in matches:
            df.loc[y, "company_name"] = df.iloc[x]["company_name"]
            df.loc[y, "match"] = ""

    # === BACK TO POLARS FOR AGGREGATION ===

    pl_df = to_polars(df[["company_name", "contribution_count"]])

    # Group by company name and sum contributions
    pl_grouped = pl_df.group_by("company_name").agg(pl.col("contribution_count").sum()).sort("contribution_count")

    # Convert small contributors to "Other"
    pl_grouped = pl_grouped.with_columns(
        pl.when(pl.col("contribution_count") <= num)
        .then(pl.lit("Other"))
        .otherwise(pl.col("company_name"))
        .alias("company_name")
    )

    # Final grouping
    pl_result = pl_grouped.group_by("company_name").agg(pl.col("contribution_count").sum()).sort("contribution_count")

    return to_pandas(pl_result)


def fuzzy_match(df, name):
    """
    This function compares each row to all of the other values in the company_name column and
    outputs a list on if there is a fuzzy match between the different rows. This gives the values
    necessary for the loop to change the company name if there is a match. 70 is the match value
    threshold for the partial ratio to be considered a match
    """
    matches = df.apply(lambda row: (fuzz.partial_ratio(row["company_name"], name, score_cutoff=70) >= 70), axis=1)
    return [i for i, x in enumerate(matches) if x]


def create_figure(df: pd.DataFrame):
    # graph generation
    fig = px.pie(
        df,
        names="company_name",
        values="contribution_count",
        color_discrete_sequence=baby_blue,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Contributions: %{value}<br><extra></extra>",
    )

    return fig
