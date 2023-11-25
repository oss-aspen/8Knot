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
from queries.pr_response_query  import pr_response_query as prrq
from queries.prs_query          import prs_query    as prsq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

PAGE = "chaoss_1"
VIZ_ID = "time-to-first-response"

time_to_first_response = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Time to First Response",
                    id=f"Bus Factor",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """This metric shows on average how longe it takes for there to be any sort of response to a pull request.\n
                            https://chaoss.community/kb/metric-time-to-first-response/
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
                dbc.Form( [
                    dbc.Row( [
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
                    ])
                ] )
                # dbc.Form(
                #     [
                #         dbc.Row(
                #             [
                #                 dbc.Label(
                #                     "Action Type:",
                #                     html_for=f"action-type-{PAGE}-{VIZ_ID}",
                #                     width="auto",
                #                 ),
                #                 dbc.Col(
                #                     [
                #                         dcc.Dropdown(
                #                             id=f"action-type-{PAGE}-{VIZ_ID}",
                #                             options=[
                #                                 {"label": "Commit", "value": "Commit"},
                #                                 {"label": "Issue Opened", "value": "Issue Opened"},
                #                                 {"label": "Issue Comment", "value": "Issue Comment"},
                #                                 {"label": "Issue Closed", "value": "Issue Closed"},
                #                                 {"label": "PR Open", "value": "PR Open"},
                #                                 {"label": "PR Review", "value": "PR Review"},
                #                                 {"label": "PR Comment", "value": "PR Comment"},
                #                             ],
                #                             value="Commit",
                #                             clearable=False,
                #                         ),
                #                         dbc.Alert(
                #                             children="""No contributions of this type have been made.\n
                #                             Please select a different contribution type.""",
                #                             id=f"check-alert-{PAGE}-{VIZ_ID}",
                #                             dismissable=True,
                #                             fade=False,
                #                             is_open=False,
                #                             color="warning",
                #                         ),
                #                     ],
                #                     className="me-2",
                #                     width=3,
                #                 ),
                #                 # dbc.Label(
                #                 #     "Top K Contributors:",
                #                 #     html_for=f"top-k-contributors-{PAGE}-{VIZ_ID}",
                #                 #     width="auto",
                #                 # ),
                #                 # dbc.Col(
                #                 #     [
                #                 #         dbc.Input(
                #                 #             id=f"top-k-contributors-{PAGE}-{VIZ_ID}",
                #                 #             type="number",
                #                 #             min=2,
                #                 #             max=100,
                #                 #             step=1,
                #                 #             value=10,
                #                 #             size="sm",
                #                 #         ),
                #                 #     ],
                #                 #     className="me-2",
                #                 #     width=2,
                #                 # ),
                #             ],
                #             align="center",
                #         ),
                #         # dbc.Row(
                #         #     [
                #         #         dbc.Label(
                #         #             "Filter Out Contributors with Keyword(s) in Login:",
                #         #             html_for=f"patterns-{PAGE}-{VIZ_ID}",
                #         #             width="auto",
                #         #         ),
                #         #         dbc.Col(
                #         #             [
                #         #                 dmc.MultiSelect(
                #         #                     id=f"patterns-{PAGE}-{VIZ_ID}",
                #         #                     placeholder="Bot filter values",
                #         #                     data=[
                #         #                         {"value": "bot", "label": "bot"},
                #         #                     ],
                #         #                     classNames={"values": "dmc-multiselect-custom"},
                #         #                     creatable=True,
                #         #                     searchable=True,
                #         #                 ),
                #         #             ],
                #         #             className="me-2",
                #         #         ),
                #         #     ],
                #         #     align="center",
                #         # ),
                #         # dbc.Row(
                #         #     [
                #         #         dbc.Col(
                #         #             [
                #         #                 dcc.DatePickerRange(
                #         #                     id=f"date-picker-range-{PAGE}-{VIZ_ID}",
                #         #                     min_date_allowed=dt.date(2005, 1, 1),
                #         #                     max_date_allowed=dt.date.today(),
                #         #                     initial_visible_month=dt.date(dt.date.today().year, 1, 1),
                #         #                     clearable=True,
                #         #                 ),
                #         #             ],
                #         #         ),
                #         #     ],
                #         #     align="center",
                #         #     justify="between",
                #         # ),
                #     ]
                # ),
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
    #Input(f"top-k-contributors-{PAGE}-{VIZ_ID}", "value"),
    Input(f"action-type-{PAGE}-{VIZ_ID}", "value"),
)
def graph_title(action_type):
    title = f"Time between pull request and first response back"
    return title


# callback for contrib-importance graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        # Input(f"action-type-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"top-k-contributors-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"patterns-{PAGE}-{VIZ_ID}", "value"),
        # Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        # Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)
def bus_factor_graph(repolist):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df1 = cache.grabm(func=prrq, repos=repolist)
    df2 = cache.grabm(func=prsq, repos=repolist)
    while df1 is None or df2 is None:
        time.sleep(1.0)
        df1 = cache.grabm(func=prrq, repos=repolist)
        df2 = cache.grabm(func=prsq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")
    # test if there is data
    if df1.empty or df2.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False
    # function for all data pre processing
    df = process_data(df1,df2)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df1: pd.DataFrame, df2: pd.DataFrame,):
    df1['msg_timestamp'] = pd.to_datetime(df1['msg_timestamp'])
    df2['created'] = pd.to_datetime(df2['created'])
    
    # Get the first response
    df1_sorted = df1.sort_values(by=['msg_timestamp'], ascending=False).groupby('pull_request_id').first().reset_index()

    # Merge dataframes on 'pull_request_id'
    merged_df = pd.merge(df1_sorted, df2, how='inner', left_on='pull_request_id', right_on='pull_request')

    # Calculate the time difference in hours
    merged_df['time_difference_hours'] = (merged_df['msg_timestamp'] - merged_df['created']).dt.total_seconds() / 3600

    # Group by the month of creation and calculate the average time difference
    result_df = merged_df.groupby(merged_df['created'].dt.to_period("M"))['time_difference_hours'].mean().reset_index()

    # Rename the columns for clarity
    result_df.columns = ['Month', 'Average_Time_Difference_Hours']
    result_df['Month'] = result_df['Month'].dt.to_timestamp()
    result_df = result_df[result_df['Month'].dt.strftime('%Y-%m') != '2013-07']

    return result_df


def create_figure(df: pd.DataFrame):
    # create plotly express pie chart
    fig = px.line(
        df,
        x="Month",
        y="Average_Time_Difference_Hours",
        color_discrete_sequence=color_seq
    )

    fig.add_trace(
        go.Scatter(
            x=df["Month"],
            y=df["Average_Time_Difference_Hours"],
            mode="lines",
            marker=dict(color=color_seq[4]),
            name="Average time to first response",
        )
    )

    # add legend title
    fig.update_layout(legend_title_text="Average time to first response")

    return fig