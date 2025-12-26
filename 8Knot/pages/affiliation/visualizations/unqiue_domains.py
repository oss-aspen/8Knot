from dash import dcc, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import baby_blue
from queries.affiliation_query import affiliation_query as aq
from pages.utils.job_utils import nodata_graph
from pages.utils.query_status import load_query_data
import datetime as dt
import app
from components.visualization import VisualizationAIO

PAGE = "affiliation"
VIZ_ID = "unique-domains"

gc_unique_domains = VisualizationAIO(
    PAGE,
    VIZ_ID,
    title="Unique Contributor Email Domains",
    graph_info="""
    Visualizes the population of unique commit email addresses per represented domain.\n
    e.g. if there are 100 distinct commit contributors and 50 use an '@gmail.com' email address,\n
    and another 50 use an '@redhat.com' email address, 50 percent of of emails wll be '@gmail.com'\n
    and 50% will be '@redhat.com'.
    """,
    controls=[
        dbc.Label(
            "Contributors Required:",
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
                value=3,
                size="sm",
                className="dark-input",
            ),
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
    class_name="dark-card",
    id="unique-domains",
)


# callback for Company Affiliation by Github Account Info graph
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
def unique_domains_graph(repolist, num, start_date, end_date, bot_switch):
    # Wait for and load query data (includes timeout, error handling, and validation)
    df = load_query_data(aq, repolist, VIZ_ID)
    if df is None:
        return nodata_graph

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df = process_data(df, num, start_date, end_date)

    fig = create_figure(df)
    return fig


def process_data(df: pd.DataFrame, num, start_date, end_date):
    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created_at", axis=0, ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.created_at >= start_date]
    if end_date is not None:
        df = df[df.created_at <= end_date]

    # creates list of unique emails and flattens list result
    emails = df.email_list.str.split(" , ").explode("email_list").unique().tolist()

    # remove any entries not in email format and put all emails in lowercase
    emails = [x.lower() for x in emails if "@" in x]

    # creates list of email domains from the emails list
    email_domains = [x[x.rindex("@") + 1 :] for x in emails]

    # creates df of domains and counts
    df = pd.DataFrame(email_domains, columns=["domains"]).value_counts().to_frame().reset_index()

    df = df.rename(columns={"count": "occurences"})

    # changes the name of the company if under a certain threshold
    df.loc[df.occurences <= num, "domains"] = "Other"

    # groups others together for final counts
    df = (
        df.groupby(by="domains")["occurences"]
        .sum()
        .reset_index()
        .sort_values(by=["occurences"], ascending=False)
        .reset_index(drop=True)
    )

    return df


def create_figure(df: pd.DataFrame):
    # graph generation
    fig = px.pie(df, names="domains", values="occurences", color_discrete_sequence=baby_blue)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Contributors: %{value}<br><extra></extra>",
    )

    return fig
