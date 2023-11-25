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
from queries.commits_query import commits_query as ctq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

PAGE = "chaoss_1"
VIZ_ID = "bus-factor-pie"

gc_bus_factor_pie = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Bus Factor",
                    id=f"Bus Factor",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """This visualization gives a view into the makeup of the contributers of a project\n
                            by the number of total commits they are making, to give insight into the overall health\n
                            of the maintainence of the project.\n
                            https://chaoss.community/kb/metric-bus-factor/
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
                        # dbc.Row(
                        #     [
                        #         dbc.Label(
                        #             "Action Type:",
                        #             html_for=f"action-type-{PAGE}-{VIZ_ID}",
                        #             width="auto",
                        #         ),
                        #         dbc.Col(
                        #             [
                        #                 dcc.Dropdown(
                        #                     id=f"action-type-{PAGE}-{VIZ_ID}",
                        #                     options=[
                        #                         {"label": "Commit", "value": "Commit"},
                        #                         {"label": "Issue Opened", "value": "Issue Opened"},
                        #                         {"label": "Issue Comment", "value": "Issue Comment"},
                        #                         {"label": "Issue Closed", "value": "Issue Closed"},
                        #                         {"label": "PR Open", "value": "PR Open"},
                        #                         {"label": "PR Review", "value": "PR Review"},
                        #                         {"label": "PR Comment", "value": "PR Comment"},
                        #                     ],
                        #                     value="Commit",
                        #                     clearable=False,
                        #                 ),
                        #                 dbc.Alert(
                        #                     children="""No contributions of this type have been made.\n
                        #                     Please select a different contribution type.""",
                        #                     id=f"check-alert-{PAGE}-{VIZ_ID}",
                        #                     dismissable=True,
                        #                     fade=False,
                        #                     is_open=False,
                        #                     color="warning",
                        #                 ),
                        #             ],
                        #             className="me-2",
                        #             width=3,
                        #         ),
                        #         dbc.Label(
                        #             "Top K Contributors:",
                        #             html_for=f"top-k-contributors-{PAGE}-{VIZ_ID}",
                        #             width="auto",
                        #         ),
                        #         dbc.Col(
                        #             [
                        #                 dbc.Input(
                        #                     id=f"top-k-contributors-{PAGE}-{VIZ_ID}",
                        #                     type="number",
                        #                     min=2,
                        #                     max=100,
                        #                     step=1,
                        #                     value=10,
                        #                     size="sm",
                        #                 ),
                        #             ],
                        #             className="me-2",
                        #             width=2,
                        #         ),
                        #     ],
                        #     align="center",
                        # ),
                        # dbc.Row(
                        #     [
                        #         dbc.Label(
                        #             "Filter Out Contributors with Keyword(s) in Login:",
                        #             html_for=f"patterns-{PAGE}-{VIZ_ID}",
                        #             width="auto",
                        #         ),
                        #         dbc.Col(
                        #             [
                        #                 dmc.MultiSelect(
                        #                     id=f"patterns-{PAGE}-{VIZ_ID}",
                        #                     placeholder="Bot filter values",
                        #                     data=[
                        #                         {"value": "bot", "label": "bot"},
                        #                     ],
                        #                     classNames={"values": "dmc-multiselect-custom"},
                        #                     creatable=True,
                        #                     searchable=True,
                        #                 ),
                        #             ],
                        #             className="me-2",
                        #         ),
                        #     ],
                        #     align="center",
                        # ),
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
)
def graph_title(k):
    title = f"Bus Factor"
    return title


# callback for contrib-importance graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "start_date"),
        Input(f"date-picker-range-{PAGE}-{VIZ_ID}", "end_date"),
    ],
    background=True,
)
def bus_factor_graph(repolist, start_date, end_date):
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

    # function for all data pre processing
    df = process_data(df, start_date, end_date)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, start_date, end_date):
    # convert to datetime objects rather than strings
    df["date"] = pd.to_datetime(df["date"], utc=True)

    # order values chronologically by created_at date
    df = df.sort_values(by="date", ascending=True)

    # filter values based on date picker
    if start_date is not None:
        df = df[df.date >= start_date]
    if end_date is not None:
        df = df[df.date <= end_date]

    # Extract month from the 'date' column
    df['month'] = df['date'].dt.to_period('M')

    # Create a DataFrame for the count of occurrences of each author email per month
    result_df = df.groupby(['month', 'author_email']).size().reset_index(name='commit_count')

    # Initialize a new DataFrame to store the results
    authors_for_50_percent_df = pd.DataFrame(columns=['month', 'num_authors_for_50_percent'])

    # Loop through each unique month in the result_df
    for month in result_df['month'].unique():
        # Filter the result_df for the current month
        result_df_monthly = result_df[result_df['month'] == month]
        
        # Sort the result_df by 'commit_count' in descending order
        result_df_monthly_sorted = result_df_monthly.sort_values(by='commit_count', ascending=False)
        
        # Calculate the cumulative sum of 'commit_count'
        result_df_monthly_sorted['cumulative_sum'] = result_df_monthly_sorted['commit_count'].cumsum()
        
        # Find the index where the cumulative sum crosses 50% of the total sum
        index_50_percent = (result_df_monthly_sorted['cumulative_sum'] >= result_df_monthly_sorted['commit_count'].sum() * 0.5).idxmax()
        
        # Get the number of authors required to reach 50%
        num_authors_for_50_percent = result_df_monthly_sorted.loc[:index_50_percent].shape[0]
        
        # Append the result to the new DataFrame
        authors_for_50_percent_df = authors_for_50_percent_df.append({'month': month, 'num_authors_for_50_percent': num_authors_for_50_percent}, ignore_index=True)

    authors_for_50_percent_df['month'] = authors_for_50_percent_df['month'].astype(str)

    # rename Action column to action_type
    df = df.rename(columns={"author_email": "Author Email"})
    # # get the number of total contributions
    # t_sum = df[action_type].sum()

    # # index df to get first k rows
    # df = df.head(top_k)

    # # convert cntrb_id from type UUID to String
    # df["cntrb_id"] = df["cntrb_id"].apply(lambda x: str(x).split("-")[0])

    # # get the number of total top k contributions
    # df_sum = df[action_type].sum()

    # # calculate the remaining contributions by taking the the difference of t_sum and df_sum
    # df = df.append({"cntrb_id": "Other", action_type: t_sum - df_sum}, ignore_index=True)

    return authors_for_50_percent_df


def create_figure(df: pd.DataFrame):
    # create plotly express pie chart
    fig = px.line(
        df,
        x="month",
        y="num_authors_for_50_percent",
        color_discrete_sequence=color_seq
    )

    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=df["num_authors_for_50_percent"],
            mode="lines",
            marker=dict(color=color_seq[4]),
            name="bus factor",
        )
    )

    # add legend title
    fig.update_layout(legend_title_text="Bus factor")

    return fig