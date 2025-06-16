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
from queries.affiliation_query import affiliation_query as aq
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt
from fuzzywuzzy import fuzz
import app
import cache_manager.cache_facade as cf

PAGE = "affiliation"
VIZ_ID = "gh-org-affiliation"

gc_gh_org_affiliation = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Organization Affiliation by GitHub Account Info",
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
                        dbc.PopoverHeader(
                            "Graph Info:",
                            style={
                                "backgroundColor": "#404040",
                                "color": "white",
                                "border": "none",
                                "borderBottom": "1px solid #606060",
                                "fontSize": "16px",
                                "fontWeight": "600",
                                "padding": "12px 16px"
                            }
                        ),
                        dbc.PopoverBody(
                            """
                            Visualizes GitHub account institution affiliation.\n
                            Many individuals don't report an affiliated institution, but\n
                            this count may be considered an absolute lower-bound on affiliation.
                            """
                        ,
                            style={
                                "backgroundColor": "#292929",
                                "color": "#E0E0E0",
                                "border": "none",
                                "fontSize": "14px",
                                "lineHeight": "1.5",
                                "padding": "16px"
                            }
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
                                    [
                                        dbc.Label(
                                            "Contributions Required:",
                                            html_for=f"contributions-required-{PAGE}-{VIZ_ID}",
                                            style={"marginBottom": "8px", "fontSize": "14px"}
                                        ),
                                        dbc.Input(
                                            id=f"contributions-required-{PAGE}-{VIZ_ID}",
                                            type="number",
                                            min=1,
                                            max=50,
                                            step=1,
                                            value=5,
                                            size="sm",
                                            className="dark-input",
                                            style={"width": "80px"},
                                        ),
                                    ],
                                    width="auto",
                                    className="me-4"
                                ),
                                dbc.Col(
                                    [
                                        # dbc.Label(
                                        #     "Date Range:",
                                        #     style={"marginBottom": "8px", "fontSize": "14px"}
                                        # ),
                                        dcc.DatePickerRange(
                                            id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                                            min_date_allowed=dt.date(2005, 1, 1),
                                            max_date_allowed=dt.date.today(),
                                            initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                                            clearable=True,
                                            style={
                                                "marginTop" : "29px",
                                            }
                                        ),
                                    ],
                                    width="auto"
                                ),
                            ],
                            justify="start",
                        ),
                    ]
                ),
            ],
            style={"padding": "2rem"}
        )
    ],
    style={"backgroundColor": "#292929", "borderRadius": "15px", "border": "1px solid #404040"},
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
        Input("bot-switch", "value"),
    ],
    background=True,
)
def gh_org_affiliation_graph(repolist, num, start_date, end_date, bot_switch):
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
    df = process_data(df, num, start_date, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, num, start_date, end_date):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""

    # convert to datetime objects rather than strings
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created_at", axis=0, ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.created_at >= start_date]
    if end_date is not None:
        df = df[df.created_at <= end_date]

    # intital count of same company name in github profile
    result = df.cntrb_company.value_counts(dropna=False)

    # reset format for df work
    df = result.to_frame()
    df["company_name"] = df.index
    df = df.reset_index()
    df["company_name"] = df["company_name"].astype(str)
    df = df.rename(columns={"cntrb_company": "orginal_name", "count": "contribution_count"})

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
    df.loc[df["contribution_count"] <= num, "company_name"] = "Other"

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
        domain=dict(x=[0, 0.45]),  # Position pie chart
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label} <br>Contributions: %{value}<br><extra></extra>",
    )
    
    fig.update_layout(
        legend_title_text="Organizations",
        plot_bgcolor="#292929",
        paper_bgcolor="#292929",
        legend=dict(
            orientation="v",
            x=0.42,  # Legend starts right after the pie chart
            y=0.5,
            xanchor="left",
            yanchor="middle"
        ),
        font=dict(
            family="Inter, sans-serif",
            size=14,
            color="white"
        ),
        margin=dict(r=50, l=50, t=50, b=50)
    )

    return fig
