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
import app
import cache_manager.cache_facade as cf

PAGE = "affiliation"
VIZ_ID = "organization-associated-activity"

gc_org_associated_activity = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Organization Associated Activity",
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
                            For non-commit contributions (see definition of Contribution on Info page)\n
                            we only know which contributor account contributed. We don't know which email,\n
                            and therefore which possible institution the contribution represented.\n
                            e.g. if we know that a PR comment was made by JaneDoe, and they have a '@redhat.com' and\n
                            an '@gmail.com' email, we don't know whether they contributed individually\n
                            or as a representative of an instituion. Therefore, we lower-bound the contribution\n
                            of representation by counting each contribution as being made by ALL of the contributors\n
                            linked email domains.\n
                            This graph can therefore be interpreted as 'The minimum number of individuals who have\n
                            been associated with each domain.'\n
                            e.g. If there are 100 contributions and 20 contributors, and each contributor has an '@redhat.com'\n
                            email associated with their account and one other random email, '@redhat.com' will be counted 100 times\n
                            and the other contributor emails will also total a count of 100.\n
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
                                        max=100,
                                        step=1,
                                        value=10,
                                        size="sm",
                                        className="dark-input",
                                    ),
                                    className="me-2",
                                    width=2,
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
                            justify="start",
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
                                    width=7,
                                ),
                            ],
                            justify="start",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        )
    ],
    className="dark-card",
    id="org-activity",
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
        Input(f"email-filter-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def org_associated_activity_graph(repolist, num, start_date, end_date, email_filter, bot_switch):
    """Each contribution is associated with a contributor. That contributor can be associated with

    more than one different email. Hence each contribution is associated with all of the emails that a contributor has historically used.

    We don't always know which email (and therefore which organization) a contributor is affiliated with at contribution

    time, so we choose to count all of their possible affiliations via their email list. e.g. if "Jane Doe" is associated with "gmail.com"

    and "yahoo.com" and they have 5 contributions, "gmail.com" and "yahoo.com" would be counted 5 times each. We assume that relatively few people

    will have many emails. We acknowledge that this will almost always contribute to an overcount but will never undercount."
    """

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
    df = process_data(df, num, start_date, end_date, email_filter)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, num, start_date, end_date, email_filter):
    """
    Process organization associated activity data using Polars for performance.

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

    # Split email lists and explode using Polars
    pl_emails = pl_df.select(pl.col("email_list").str.split(" , ").explode().alias("email")).filter(
        pl.col("email").str.contains("@")
    )

    # Extract domains using Polars string operations
    pl_domains = pl_emails.with_columns(
        pl.col("email").str.to_lowercase().str.extract(r"@(.+)$", 1).alias("domains")
    ).filter(pl.col("domains").is_not_null())

    # Count domains
    pl_counts = pl_domains.group_by("domains").agg(pl.len().alias("occurrences"))

    # Replace low-count domains with "Other"
    pl_counts = pl_counts.with_columns(
        pl.when(pl.col("occurrences") <= num).then(pl.lit("Other")).otherwise(pl.col("domains")).alias("domains")
    )

    # Group by domains (consolidating "Other")
    pl_result = pl_counts.group_by("domains").agg(pl.col("occurrences").sum()).sort("occurrences", descending=True)

    # Remove "Other" from set
    pl_result = pl_result.filter(pl.col("domains") != "Other")

    # Apply email filters
    if email_filter is not None:
        if "gmail" in email_filter:
            pl_result = pl_result.filter(pl.col("domains") != "gmail.com")
        if "github" in email_filter:
            pl_result = pl_result.filter(pl.col("domains") != "users.noreply.github.com")

    # === POLARS PROCESSING END ===

    # Convert to Pandas for visualization
    return to_pandas(pl_result)


def create_figure(df: pd.DataFrame):
    # graph generation
    fig = px.bar(df, x="domains", y="occurrences", color_discrete_sequence=[baby_blue[8]])
    fig.update_xaxes(rangeslider_visible=True, range=[-0.5, 15])
    fig.update_layout(
        xaxis_title="Domains",
        yaxis_title="Contributions",
        bargroupgap=0.1,
        margin_b=40,
        font=dict(size=14),
    )
    fig.update_traces(
        hovertemplate="%{label} <br>Contributions: %{value}<br><extra></extra>",
    )

    return fig
