from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
from queries.ossf_score_query import ossf_score_query as osq
import io
import cache_manager.cache_facade as cf
from pages.utils.job_utils import nodata_graph
import time
from datetime import datetime

PAGE = "repo_info"
VIZ_ID = "ossf-scorecard"

gc_ossf_scorecard = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "OSSF Scorecard",
                                className="card-title",
                                style={"textAlign": "left", "fontSize": "20px", "color": "white"},
                            ),
                            width=10,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Scorecard Info",
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
                                    "boxShadow": "none"
                                }
                            ),
                            width=2,
                            className="d-flex justify-content-end",
                        ),
                    ],
                    align="center",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Link to details about checks:"),
                        dbc.PopoverBody("https://github.com/ossf/scorecard?tab=readme-ov-file#what-is-scorecard"),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    html.Div(id=f"{PAGE}-{VIZ_ID}"),
                ),
                html.Hr(style={
                    "borderColor": "#e0e0e0", 
                    "margin": "1.5rem -2rem", 
                    "width": "calc(100% + 4rem)",
                    "marginLeft": "-2rem"
                }),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Label(
                                        ["Last Updated: ", html.Span(id=f"{PAGE}-{VIZ_ID}-updated")],
                                        style={"fontSize": "14px"}
                                    ),
                                    width="auto",
                                ),
                            ],
                            justify="start",
                        ),
                    ]
                ),
            ]
        )
    ],
    style={
        "padding": "20px",
        "borderRadius": "10px",
        "backgroundColor": "#292929",
        "border": "1px solid #404040"
    },
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


# callback for ossf scorecard
@callback(
    [Output(f"{PAGE}-{VIZ_ID}", "children"), Output(f"{PAGE}-{VIZ_ID}-updated", "children")],
    [
        Input("repo-info-selection", "value"),
    ],
    background=True,
)
def ossf_scorecard(repo):
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=osq.__name__, repolist=[repo]):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # GET ALL DATA FROM POSTGRES CACHE
    df = cf.retrieve_from_cache(
        tablename=osq.__name__,
        repolist=[repo],
    )

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True), dbc.Label("No data")

    # repo id not needed for table
    df.drop(["repo_id"], axis=1, inplace=True)

    # get all values from the data_collection_date column
    updated_times = pd.to_datetime(df["data_collection_date"])

    # we dont need to display this column for every entry
    df.drop(["data_collection_date"], axis=1, inplace=True)

    df.loc[df.name == "OSSF_SCORECARD_AGGREGATE_SCORE", "name"] = "Aggregate Score"
    df.sort_values("name", ascending=True, inplace=True)
    df.rename(columns={"name": "Check Type", "score": "Score"}, inplace=True)

    table = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)

    unique_updated_times = updated_times.drop_duplicates().to_numpy().flatten()

    if len(unique_updated_times) > 1:
        logging.warning(f"{VIZ_ID} - MORE THAN ONE DATA COLLECTION DATE")

    updated_date = pd.to_datetime(str(unique_updated_times[-1])).strftime("%d/%m/%Y")

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return table, dbc.Label(updated_date)
