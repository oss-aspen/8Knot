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

PAGE = "company"
VIZ_ID = "company-associated-activity"

gc_company_associated_activity = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Company Associated Activity",
                    className="card-title",
                    style={"textAlign": "center"},
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
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Contributions Required:",
                                    html_for=f"company-contributions-required-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"company-contributions-required-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=100,
                                        step=1,
                                        value=10,
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
        Input(f"company-contributions-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)
def compay_associated_activity_graph(repolist, num, start_date, end_date):
    """Each contribution is associated with a contributor. That contributor can be associated with

    more than one different email. Hence each contribution is associated with all of the emails that a contributor has historically used.

    We don't always know which email (and therefore which organization) a contributor is affiliated with at contribution

    time, so we choose to count all of their possible affiliations via their email list. e.g. if "Jane Doe" is associated with "gmail.com"

    and "yahoo.com" and they have 5 contributions, "gmail.com" and "yahoo.com" would be counted 5 times each. We assume that relatively few people

    will have many emails. We acknowledge that this will almost always contribute to an overcount but will never undercount."
    """

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
    # convert to datetime objects rather than strings
    df["created"] = pd.to_datetime(df["created"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created", axis=0, ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.created >= start_date]
    if end_date is not None:
        df = df[df.created <= end_date]

    # creates list of emails for each contribution and flattens list result
    emails = df.email_list.str.split(" , ").explode("email_list").tolist()

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
    fig = px.bar(df, x="domains", y="occurrences", color_discrete_sequence=color_seq)
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
