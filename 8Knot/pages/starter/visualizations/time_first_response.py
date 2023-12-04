from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px
from pages.utils.graph_utils import color_seq
from queries.contributors_query import contributors_query as ctq
from cache_manager.cache_manager import CacheManager as cm
import io
import time
from pages.utils.job_utils import nodata_graph

PAGE = "starter"
VIZ_ID = "time-first-response"

gc_time_first_response = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Time To First Response",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes the closed of new issue to a project\n
                            and differentiates them by their first response in-project action.
                            """
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
                dbc.Row(
                    dbc.Button(
                        "About Graph",
                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                        color="secondary",
                        size="small",
                    ),
                    style={"paddingTop": ".5em"},
                ),
            ]
        ),
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


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
    ],
    background=True,
)
def create_time_first_response_graph(repolist):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    start = time.perf_counter()
    logging.warning("CONTRIB_DRIVE_REPEAT_VIZ - START")

    # test if there is data
    if df.empty:
        logging.warning("1ST CONTRIBUTIONS - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df = process_data(df)

    fig = create_figure(df)

    logging.warning(f"1ST_CONTRIBUTIONS_VIZ - END - {time.perf_counter() - start}")
    return fig


def process_data(df):
    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df.rename(columns={"created_at": "created"}, inplace=True)

    # selection for specific actions ("pr comment" and "issue closed")
    allowed_actions = ["PR Comment", "Issue Closed"]
    df = df[df["Action"].isin(allowed_actions)]

    # reset index to be ready for plotly
    df = df.reset_index()

    return df

def create_figure(df):
    # Define your own color sequence for "PR Comment" and "Issue Closed"
    color_sequence = ["#1f77b4", "#ff7f0e"]  # Blue for "PR Comment", Orange for "Issue Closed"

    # create plotly express histogram
    fig = px.histogram(df, x="created", color="Action", color_discrete_sequence=color_sequence)

    # creates bins with 12 month size (1 year) and customizes the hover value for the bars
    fig.update_traces(
        xbins_size="M12",
        hovertemplate="Date: %{x}" + "<br>Amount: %{y}",
    )

    # update xaxes to align for the 12 month bin size
    fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M12")

    # layout styling
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Contributions",
        margin_b=40,
        font=dict(size=14),
    )

    return fig
