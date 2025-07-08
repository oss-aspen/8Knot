from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.contributors_query import contributors_query as ctq
from pages.utils.job_utils import nodata_graph
import time
import app
import pages.utils.preprocessing_utils as preproc_utils
import cache_manager.cache_facade as cf


PAGE = "contributors"
VIZ_ID = "contribs-by-action"

gc_contribs_by_action = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Contributors by Action Type",
                                className="card-title",
                                style={"textAlign": "left", "fontSize": "20px", "color": "white"},
                            ),
                            width=10,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                className="text-white font-medium rounded-lg px-3 py-1.5 transition-all duration-200 cursor-pointer text-sm custom-hover-button",
                                style={
                                    "backgroundColor": "#292929",
                                    "borderColor": "#404040",
                                    "color": "white",
                                    "borderRadius": "20px",
                                    "padding": "6px 12px",
                                    "fontSize": "14px",
                                    "fontWeight": "500",
                                    "border": "1px solid #404040",
                                    "cursor": "pointer",
                                    "transition": "all 0.2s ease",
                                    "backgroundImage": "none",
                                    "boxShadow": "none",
                                },
                            ),
                            width=2,
                            className="d-flex justify-content-end",
                        ),
                    ],
                    align="center",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """Visualizes the number of contributors who have performed a specific action\n
                            (have opened a PR, for example) within a specified time-window. This is different\n
                            from counting the number of contributions (the number of PRs having been opened)-\n
                            the focus is on the activity of distinct contributors. """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                html.Hr(
                    style={
                        "borderColor": "#404040",
                        "borderWidth": "1px",
                        "opacity": "0.3",
                        "margin": "1.5rem 0",
                    }
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Action Type:",
                                            html_for=f"action-dropdown-{PAGE}-{VIZ_ID}",
                                            style={"marginBottom": "8px", "fontSize": "14px"},
                                        ),
                                        dbc.Select(
                                            id=f"action-dropdown-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "PR Open", "value": "PR Opened"},
                                                {"label": "Comment", "value": "Comment"},
                                                {"label": "PR Review", "value": "PR Review"},
                                                {"label": "Issue Opened", "value": "Issue Opened"},
                                                {"label": "Issue Closed", "value": "Issue Closed"},
                                                {"label": "Commit", "value": "Commit"},
                                            ],
                                            value="PR Opened",
                                            size="sm",
                                            style={
                                                "fontSize": "14px",
                                                "backgroundColor": "#404040",
                                                "borderColor": "#404040",
                                                "color": "white",
                                                "height": "32px",
                                                "padding": "4px 8px",
                                            },
                                        ),
                                    ],
                                    width="auto",
                                    className="me-4",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Date Interval:",
                                            html_for=f"date-interval-{PAGE}-{VIZ_ID}",
                                            style={"marginBottom": "8px", "fontSize": "14px"},
                                        ),
                                        dbc.RadioItems(
                                            id=f"date-interval-{PAGE}-{VIZ_ID}",
                                            className="modern-radio-buttons-small",
                                            options=[
                                                {"label": "Month", "value": "M1"},
                                                {"label": "Quarter", "value": "M3"},
                                                {"label": "6 Months", "value": "M6"},
                                                {"label": "Year", "value": "M12"},
                                            ],
                                            value="M1",
                                            inline=True,
                                        ),
                                    ],
                                    width="auto",
                                ),
                            ],
                            justify="start",
                        ),
                        dbc.Alert(
                            children="""No contributions of this type have been made.\n
                            Please select a different contribution type.""",
                            id=f"check-alert-{PAGE}-{VIZ_ID}",
                            dismissable=True,
                            fade=False,
                            is_open=False,
                            color="warning",
                            style={"marginTop": "1rem"},
                        ),
                    ]
                ),
            ]
        )
    ],
    style={"padding": "20px", "borderRadius": "10px", "backgroundColor": "#292929", "border": "1px solid #404040"},
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


# callback for contributors by action graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"date-interval-{PAGE}-{VIZ_ID}", "value"),
        Input(f"action-dropdown-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def contribs_by_action_graph(repolist, interval, action, bot_switch):
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
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # checks if there is a contribution of a specfic action in repo set
    if not df["Action"].str.contains(action).any():
        return dash.no_update, True

    # function for all data pre processing
    df = process_data(df, interval, action)

    fig = create_figure(df, interval, action)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, interval, action):
    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created_at", axis=0, ascending=True)

    # drop all contributions that are not the selected action
    df = df[df["Action"].str.contains(action)]

    return df


def create_figure(df: pd.DataFrame, interval, action):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # create plotly express histogram
    fig = px.histogram(df, x="created_at", color_discrete_sequence=[color_seq[3]])

    # creates bins with interval size and customizes the hover value for the bars
    fig.update_traces(
        xbins_size=interval,
        hovertemplate=hover + "<br>" + action + " Contributors: %{y}<br><extra></extra>",
        marker_line_width=0.1,
        marker_line_color="black",
    )

    # update xaxes to align for the interval bin size
    fig.update_xaxes(
        showgrid=True,
        ticklabelmode="period",
        dtick=period,
        rangeslider_yaxis_rangemode="match",
        range=x_r,
    )

    # layout styling
    fig.update_layout(
        xaxis_title=x_name,
        yaxis_title="Contributors",
        margin_b=40,
        font=dict(size=14),
        plot_bgcolor="#292929",
        paper_bgcolor="#292929",
    )

    return fig
