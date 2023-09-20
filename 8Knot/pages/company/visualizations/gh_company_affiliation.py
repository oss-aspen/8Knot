from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import color_seq
from queries.company_query import company_query as cmq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
from fuzzywuzzy import fuzz

PAGE = "company"
VIZ_ID = "gh-company-affiliation"

gc_gh_company_affiliation = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Company Affiliation by Github Account Info",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes Github account institution affiliation.\n
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
                ),
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
                                    ),
                                    width="auto",
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
                            justify="between",
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


# callback for Company Affiliation by Github Account Info graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"contributions-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)
def gh_company_affiliation_graph(repolist, num, start_date, end_date):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=cmq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=cmq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, num, start_date, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, num, start_date, end_date):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""

    # convert to datetime objects rather than strings
    df["created"] = pd.to_datetime(df["created"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.created >= start_date]
    if end_date is not None:
        df = df[df.created <= end_date]

    # intital count of same company name in github profile
    result = df.cntrb_company.value_counts(dropna=False)

    # reset format for df work
    df = result.to_frame()
    df["company_name"] = df.index
    df = df.reset_index()
    df["company_name"] = df["company_name"].astype(str)
    df = df.rename(columns={"index": "orginal_name", "cntrb_company": "contribution_count"})

    # applies fuzzy matching comparing all rows to each other
    df["match"] = df.apply(lambda row: fuzzy_match(df, row["company_name"]), axis=1)

    # changes company name to match other fuzzy matches
    for x in range(0, len(df)):
        # gets match values for the current row
        matches = df.iloc[x]["match"]
        for y in matches:
            # for each match, change the name to its match and clear out match column as
            # it will unnecessarily reapply changes
            df.loc[y, "company_name"] = df.iloc[x]["company_name"]
            df.loc[y, "match"] = ""

    # groups all same name company affiliation and sums the contributions
    df = (
        df.groupby(by="company_name")["contribution_count"]
        .sum()
        .reset_index()
        .sort_values(by=["contribution_count"])
        .reset_index(drop=True)
    )

    # changes the name of the company if under a certain threshold
    df.loc[df.contribution_count <= num, "company_name"] = "Other"

    # groups others together for final counts
    df = (
        df.groupby(by="company_name")["contribution_count"]
        .sum()
        .reset_index()
        .sort_values(by=["contribution_count"])
        .reset_index(drop=True)
    )

    return df


def fuzzy_match(df, name):
    """
    This function compares each row to all of the other values in the company_name column and
    outputs a list on if there is a fuzzy match between the different rows. This gives the values
    necessary for the loop to change the company name if there is a match. 70 is the match value
    threshold for the partial ratio to be considered a match
    """
    matches = df.apply(lambda row: (fuzz.partial_ratio(row["company_name"], name) >= 70), axis=1)
    return [i for i, x in enumerate(matches) if x]


def create_figure(df: pd.DataFrame):
    # graph generation
    fig = px.pie(
        df,
        names="company_name",
        values="contribution_count",
        color_discrete_sequence=color_seq,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Contributions: %{value}<br><extra></extra>",
    )

    return fig
