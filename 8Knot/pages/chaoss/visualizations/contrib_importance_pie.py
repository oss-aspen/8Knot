from dash import html, dcc, callback
import dash
from dash import dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.contributors_query import contributors_query as ctq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

PAGE = "chaoss"
VIZ_ID = "contrib-importance-pie"

gc_contrib_importance_pie = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    id=f"graph-title-{PAGE}-{VIZ_ID}",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                                        For a given action type, visualizes the proportional share of the top k anonymous
                                        contributors, aggregating the remaining contributors as "Other". Suppose Contributor A
                                        opens the most PRs of all contributors, accounting for 1/5 of all PRs. If k = 1,
                                        then the chart will have one slice for Contributor A accounting for 1/5 of the area,
                                        with the remaining 4/5 representing all other contributors. By default, contributors
                                        who have 'potential-bot-filter' in their login are filtered out. Optionally, contributors
                                        can be filtered out by their logins with custom keyword(s). Note: Some commits may have a
                                        Contributor ID of 'None' if there is no Github account is associated with the email that
                                        the contributor committed as.
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
                                    "Action Type:",
                                    html_for=f"action-type-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dcc.Dropdown(
                                            id=f"action-type-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "Commit", "value": "Commit"},
                                                {"label": "Issue Opened", "value": "Issue Opened"},
                                                {"label": "Issue Comment", "value": "Issue Comment"},
                                                {"label": "Issue Closed", "value": "Issue Closed"},
                                                {"label": "PR Open", "value": "PR Open"},
                                                {"label": "PR Review", "value": "PR Review"},
                                                {"label": "PR Comment", "value": "PR Comment"},
                                            ],
                                            value="Commit",
                                            clearable=False,
                                        ),
                                        dbc.Alert(
                                            children="""No contributions of this type have been made.\n
                                            Please select a different contribution type.""",
                                            id=f"check-alert-{PAGE}-{VIZ_ID}",
                                            dismissable=True,
                                            fade=False,
                                            is_open=False,
                                            color="warning",
                                        ),
                                    ],
                                    className="me-2",
                                    width=3,
                                ),
                                dbc.Label(
                                    "Top K Contributors:",
                                    html_for=f"top-k-contributors-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Input(
                                            id=f"top-k-contributors-{PAGE}-{VIZ_ID}",
                                            type="number",
                                            min=2,
                                            max=100,
                                            step=1,
                                            value=10,
                                            size="sm",
                                        ),
                                    ],
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Filter Out Contributors with Keyword(s) in Login:",
                                    html_for=f"patterns-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dmc.MultiSelect(
                                            id=f"patterns-{PAGE}-{VIZ_ID}",
                                            placeholder="Bot filter values",
                                            data=[
                                                {"value": "bot", "label": "bot"},
                                            ],
                                            classNames={"values": "dmc-multiselect-custom"},
                                            creatable=True,
                                            searchable=True,
                                        ),
                                    ],
                                    className="me-2",
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dcc.DatePickerRange(
                                            id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                            min_date_allowed=dt.date(2005, 1, 1),
                                            max_date_allowed=dt.date.today(),
                                            initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                            clearable=True,
                                        ),
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "About Graph",
                                            id=f"popover-target-{PAGE}-{VIZ_ID}",
                                            color="secondary",
                                            size="sm",
                                        ),
                                    ],
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


# callback for dynamically changing the graph title
@callback(
    Output(f"graph-title-{PAGE}-{VIZ_ID}", "children"),
    Input(f"top-k-contributors-{PAGE}-{VIZ_ID}", "value"),
    Input(f"action-type-{PAGE}-{VIZ_ID}", "value"),
)
def graph_title(k, action_type):
    title = f"Lottery Factor: Top {k} Contributors by {action_type}"
    return title


# callback for contrib-importance graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"action-type-{PAGE}-{VIZ_ID}", "value"),
        Input(f"top-k-contributors-{PAGE}-{VIZ_ID}", "value"),
        Input(f"patterns-{PAGE}-{VIZ_ID}", "value"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)
def create_top_k_cntrbs_graph(repolist, action_type, top_k, patterns, start_date, end_date):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    # checks if there is a contribution of a specfic action type in repo set
    if not df["Action"].str.contains(action_type).any():
        return dash.no_update, True

    # function for all data pre processing
    df = process_data(df, action_type, top_k, patterns, start_date, end_date)

    fig = create_figure(df, action_type)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, action_type, top_k, patterns, start_date, end_date):
    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # order values chronologically by created_at date
    df = df.sort_values(by="created_at", ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.created_at >= start_date]
    if end_date is not None:
        df = df[df.created_at <= end_date]

    # subset the df such that it only contains rows where the Action column value is the action type
    df = df[df["Action"].str.contains(action_type)]

    # option to filter out potential bots
    if patterns:
        # remove rows where login column value contains any keyword in patterns
        patterns_mask = df["login"].str.contains("|".join(patterns), na=False)
        df = df[~patterns_mask]

    # count the number of contributions for each contributor
    df = (df.groupby("cntrb_id")["Action"].count()).to_frame()

    # sort rows according to amount of contributions from greatest to least
    df.sort_values(by="cntrb_id", ascending=False, inplace=True)
    df = df.reset_index()

    # rename Action column to action_type
    df = df.rename(columns={"Action": action_type})

    # get the number of total contributions
    t_sum = df[action_type].sum()

    # index df to get first k rows
    df = df.head(top_k)

    # convert cntrb_id from type UUID to String
    df["cntrb_id"] = df["cntrb_id"].apply(lambda x: str(x).split("-")[0])

    # get the number of total top k contributions
    df_sum = df[action_type].sum()

    # calculate the remaining contributions by taking the the difference of t_sum and df_sum
    df = df.append({"cntrb_id": "Other", action_type: t_sum - df_sum}, ignore_index=True)

    return df


def create_figure(df: pd.DataFrame, action_type):
    # create plotly express pie chart
    fig = px.pie(
        df,
        names="cntrb_id",  # can be replaced with login to unanonymize
        values=action_type,
        color_discrete_sequence=color_seq,
    )

    # display percent contributions and cntrb_id in each wedge
    # format hover template to display cntrb_id and the number of their contributions according to the action_type
    fig.update_traces(
        textinfo="percent+label",
        textposition="inside",
        hovertemplate="Contributor ID: %{label} <br>Contributions: %{value}<br><extra></extra>",
    )

    # add legend title
    fig.update_layout(legend_title_text="Contributor ID")

    return fig
