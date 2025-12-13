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
import io
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
import app
import cache_manager.cache_facade as cf

PAGE = "affiliation"
VIZ_ID = "org-core-contributors"

gc_org_core_contributors = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Organization Core Contributors",
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
                            "This graph counts the number of core contributions that COULD be linked to each organization.\n\
                            The methodology behind this is to take each associated email to someones GitHub account\n\
                            and link the contributions to each as it is unknown which initity the actvity was done for.\n\
                            Then the graph groups contributions by contributors and filters by contributors that are core.\n\
                            Contributions required is the amount of contributions necessary to be consider a core contributor\n\
                            Core Contributors required is the amount of core contributors needed to have the domain listed."
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
                                        max=100,
                                        step=1,
                                        value=10,
                                        size="sm",
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
                                ),
                                dbc.Label(
                                    "Core Contributors Required:",
                                    html_for=f"contributors-required-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"contributors-required-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=50,
                                        step=1,
                                        value=3,
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
                                dbc.Col(
                                    dcc.DatePickerRange(
                                        id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                        min_date_allowed=dt.date(2005, 1, 1),
                                        max_date_allowed=dt.date.today(),
                                        initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                        clearable=True,
                                        className="dark-date-picker",
                                    ),
                                    # style={"marginTop": "1.7rem"},
                                    width=7,
                                ),
                                dbc.Col(
                                    dbc.Checklist(
                                        id=f"email-filter-{PAGE}-{VIZ_ID}",
                                        options=[
                                            {
                                                "label": "Exclude Gmail",
                                                "value": "gmail",
                                            },
                                            {
                                                "label": "Exclude GitHub",
                                                "value": "github",
                                            },
                                        ],
                                        value=[""],
                                        inline=True,
                                        switch=True,
                                    ),
                                    width=6,
                                ),
                            ],
                            align="center",
                            justify="between",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="org-core-contributors",
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


# callback for Company Affiliation by Github Account Info graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"contributions-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"contributors-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
        Input(f"email-filter-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def compay_associated_activity_graph(
    repolist,
    contributions,
    contributors,
    start_date,
    end_date,
    email_filter,
    bot_switch,
):
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
    df = process_data(df, contributions, contributors, start_date, end_date, email_filter)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, contributions, contributors, start_date, end_date, email_filter):
    """
    Process organization core contributors data using Polars for performance.

    Follows the "Polars Core, Pandas Edge" architecture.
    """
    # === POLARS PROCESSING START ===

    # Convert to Polars for fast processing
    pl_df = to_polars(df)

    # Convert to datetime and sort
    pl_df = pl_df.with_columns(pl.col("created_at").cast(pl.Datetime("us", "UTC")))
    pl_df = pl_df.sort("created_at")

    # Filter by date range
    if start_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") >= start_date)
    if end_date is not None:
        pl_df = pl_df.filter(pl.col("created_at") <= end_date)

    # Group by contributor and count
    pl_grouped = pl_df.group_by(["cntrb_id", "email_list"]).agg(pl.len().alias("contribution_count"))

    # Filter by contribution threshold
    pl_core = pl_grouped.filter(pl.col("contribution_count") >= contributions)

    # Convert to Pandas for email processing (string operations are complex)
    df_core = to_pandas(pl_core)

    # === POLARS PROCESSING END ===

    # Email domain extraction (keeping in Pandas for complex string ops)
    emails = df_core.email_list.str.split(" , ").explode("email_list").tolist()
    emails = [x.lower() for x in emails if "@" in x]
    email_domains = [x[x.rindex("@") + 1 :] for x in emails]

    # Convert back to Polars for final aggregation
    pl_domains = pl.DataFrame({"domains": email_domains})

    # Count and group domains
    pl_counts = pl_domains.group_by("domains").agg(pl.len().alias("contributors"))

    # Apply threshold - mark small contributors as "Other"
    pl_counts = pl_counts.with_columns(
        pl.when(pl.col("contributors") <= contributors)
        .then(pl.lit("Other"))
        .otherwise(pl.col("domains"))
        .alias("domains")
    )

    # Group again to combine "Other" entries
    pl_result = (
        pl_counts.group_by("domains")
        .agg(pl.col("contributors").sum())
        .sort("contributors", descending=True)
        .filter(pl.col("domains") != "Other")
    )

    # Apply email filters
    if email_filter is not None:
        if "gmail" in email_filter:
            pl_result = pl_result.filter(pl.col("domains") != "gmail.com")
        if "github" in email_filter:
            pl_result = pl_result.filter(pl.col("domains") != "users.noreply.github.com")

    return to_pandas(pl_result)


def create_figure(df: pd.DataFrame):
    # graph generation
    fig = px.bar(df, x="domains", y="contributors", color_discrete_sequence=[baby_blue[8]])
    fig.update_xaxes(rangeslider_visible=True, range=[-0.5, 15])
    fig.update_layout(
        xaxis_title="Domains",
        yaxis_title="Core Contributors",
        bargroupgap=0.1,
        margin_b=40,
        font=dict(size=14),
    )
    fig.update_traces(
        hovertemplate="%{label} <br>Contributors: %{value}<br><extra></extra>",
    )

    return fig
