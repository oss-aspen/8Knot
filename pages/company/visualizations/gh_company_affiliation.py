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
from queries.company_query import company_query as cq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
from fuzzywuzzy import fuzz

PAGE = "company"  # EDIT FOR PAGE USED
VIZ_ID = "gh-company-affiliation"  # UNIQUE IDENTIFIER FOR CALLBAKCS, MUST BE UNIQUE

paramter_1 = "company-contributions-required"
paramter_2 = "null-check"


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
                            "This graph looks at github contributors profiles and takes in their listed company"
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
                                    html_for=paramter_1,
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=paramter_1,
                                        type="number",
                                        min=1,
                                        max=50,
                                        step=1,
                                        value=5,
                                        size="sm",
                                    ),
                                    className="me-2",
                                    width=1,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Checklist(
                                            id=paramter_2,
                                            options=[
                                                {"label": "Exclude None", "value": "none"},
                                                {"label": "Exclude Other", "value": "other"},
                                            ],
                                            value=[""],
                                            inline=True,
                                        ),
                                    ]
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
                                html.Div(id="SliderContainer"),
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


@callback(
    Output("SliderContainer", "children"),
    [
        Input("repo-choices", "data"),
    ],
    background=True,
)
def create_slider(repolist):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=cq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=cq, repos=repolist)

    # get date value for first contribution
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df = df.sort_values(by="created", axis=0, ascending=True)
    base = df.iloc[0]["created"]

    date_picker = (
        dcc.DatePickerRange(
            id="date-picker-range",
            min_date_allowed=base,
            max_date_allowed=dt.date.today(),
            clearable=True,
        ),
    )
    return date_picker


# callback for Company Affiliation by Github Account Info graph
@callback(
    Output(VIZ_ID, "figure"),
    [
        Input("repo-choices", "data"),
        Input(paramter_2, "value"),
        Input(paramter_1, "value"),
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
    ],
    background=True,
    prevent_initial_call=True,
)
def gh_company_affiliation_graph(repolist, checks, num, start_date, end_date):

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
    df = process_data(df, checks, num, start_date, end_date)

    fig = create_figure(df)

    logging.debug(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, checks, num, start_date, end_date):
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
    df["match"] = df.apply(lambda row: func(df, row["company_name"]), axis=1)

    # changes company name to match other fuzzy matches
    for x in range(0, len(df)):
        matches = df.iloc[x]["match"]
        for y in matches:
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

    # removes entries with none or other if checked
    if "none" in checks:
        df = df[df.company_name != "None"]
    if "other" in checks:
        df = df[df.company_name != "Other"]

    return df


def func(df, name):
    matches = df.apply(lambda row: (fuzz.partial_ratio(row["company_name"], name) >= 70), axis=1)
    return [i for i, x in enumerate(matches) if x]


def create_figure(df: pd.DataFrame):

    # graph generation
    fig = px.pie(df, names="company_name", values="contribution_count", color_discrete_sequence=color_seq)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Contribution: %{value}<br><extra></extra>",
    )

    return fig
