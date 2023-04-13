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
from queries.commits_query import commits_query as cq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

PAGE = "company"
VIZ_ID = "commit-domains"

paramter_1 = "company-contributions-required"


gc_commit_domains = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Commit Activity by Domain",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This graph shows the proportions of email domains that contributors used to make commits.\n\
                            e.g. johndoe@gmail.com as a commit author would contribute to the count of gmail.com once.\n\
                            NOTE: the domain might not respresent if it is done as an individual or company."
                        ),
                    ],
                    id=f"{PAGE}-popover-{VIZ_ID}",
                    target=f"{PAGE}-popover-target-{VIZ_ID}",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=VIZ_ID),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Contributions Required:",
                                    html_for=f"{PAGE}-{paramter_1}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    [
                                        dbc.Input(
                                            id=f"{PAGE}-{paramter_1}-{VIZ_ID}",
                                            type="number",
                                            min=1,
                                            max=100,
                                            step=1,
                                            value=10,
                                            size="sm",
                                        ),
                                    ],
                                    className="me-2",
                                    width=2,
                                ),
                                # pads spacing in the card
                                dbc.Col(
                                    [],
                                    width=5,
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"{PAGE}-popover-target-{VIZ_ID}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dcc.DatePickerRange(
                                    id=f"{PAGE}-date-picker-range-{VIZ_ID}",
                                    min_date_allowed=dt.date(2005, 1, 1),
                                    max_date_allowed=dt.date.today(),
                                    clearable=True,
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
    Output(f"{PAGE}-popover-{VIZ_ID}", "is_open"),
    [Input(f"{PAGE}-popover-target-{VIZ_ID}", "n_clicks")],
    [State(f"{PAGE}-popover-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for Company Affiliation by Github Account Info graph
@callback(
    Output(VIZ_ID, "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"{PAGE}-{paramter_1}-{VIZ_ID}", "value"),
        Input(f"{PAGE}-date-picker-range-{VIZ_ID}", "start_date"),
        Input(f"{PAGE}-date-picker-range-{VIZ_ID}", "end_date"),
    ],
    background=True,
    # prevent_initial_call=True,
)
def commit_domains_graph(repolist, num, start_date, end_date):

    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=cq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=cq, repos=repolist)

    start = time.perf_counter()
    logging.debug(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.debug(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    print("here 1")
    df = process_data(df, num, start_date, end_date)
    print("here 2")
    fig = create_figure(df)
    print("here 3")

    logging.debug(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, num, start_date, end_date):

    # convert to datetime objects rather than strings
    df["author_timestamp"] = pd.to_datetime(df["author_timestamp"], utc=True)

    # order values chronologically by author_timestamp date earliest to latest
    df = df.sort_values(by="author_timestamp", axis=0, ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.author_timestamp >= start_date]
    if end_date is not None:
        df = df[df.author_timestamp <= end_date]

    # creates list of emails for each contribution and flattens list result
    emails = df.committer_email.tolist()

    # remove any entries not in email format
    emails = [x for x in emails if "@" in x]

    # creates list of email domains from the emails list
    email_domains = [x[x.rindex("@") + 1 :] for x in emails]

    # creates df of domains and counts
    df = pd.DataFrame(email_domains, columns=["domains"]).value_counts().to_frame().reset_index()

    df = df.rename(columns={0: "occurrences"})

    # changes the name of the company if under a certain threshold
    df.loc[df.occurrences <= num, "domains"] = "Other"

    # groups others together for final counts
    df = (
        df.groupby(by="domains")["occurrences"]
        .sum()
        .reset_index()
        .sort_values(by=["occurrences"], ascending=False)
        .reset_index(drop=True)
    )

    return df


def create_figure(df: pd.DataFrame):

    # graph generation
    fig = px.pie(df, names="domains", values="occurrences", color_discrete_sequence=color_seq)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Contribution: %{value}<br><extra></extra>",
    )

    return fig
