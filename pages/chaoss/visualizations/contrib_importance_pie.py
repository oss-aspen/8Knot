from dash import html, dcc, callback
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
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
import random 

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
                        dbc.PopoverBody("""
                                        For a given action type, visualizes the proportional share of the top k anonymous 
                                        contributors, aggregating the remaining contributors as "Other". Suppose Contributor A 
                                        opens the most PRs of all contributors, accounting for 1/5 of all PRs. If k = 1, 
                                        then the chart will have one slice for Contributor A accounting for 1/5 of the area,
                                        with the remaining 4/5 representing all other contributors. By default, contributors
                                        who have 'potential-bot-filter' in their login are filtered out. Optionally, contributors 
                                        can be filtered out by their logins with custom keyword(s). Note: Some commits may have a 
                                        Contributor ID of 'None' if there is no Github account is associated with the email that
                                        the contributor committed as.
                                        """),
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
                    [   dbc.Row(
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
                                                {"label": "PR Open", "value": "PR Open"},
                                                {"label": "PR Review", "value": "PR Review"},
                                                {"label": "PR Comment", "value": "PR Comment"}
                                                ,
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
                                        [dbc.Input(
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
                            align = "center"
                        ),  
                        dbc.Row(
                            [   dbc.Label("Filter Out Contributors with Keyword(s) in Login:",
                                    html_for=f"patterns-{PAGE}-{VIZ_ID}",
                                    width="auto",), 
                                dbc.Col(
                                    [
                                        dcc.Dropdown(
                                            id = f"patterns-{PAGE}-{VIZ_ID}", 
                                            options = [
                                                {"value": "potential-bot-filter", "label": "potential-bot-filter"},
                                            ], 
                                            value = ['potential-bot-filter'],
                                            multi = True,
                                            searchable=True,
                                            
                                            ),

                                        dcc.Store(
                                            id = f"keyword-{PAGE}-{VIZ_ID}", #  keeps track of keys inputted into dcc.Dropdown
                                        )
                                    ], 
                                    className = "me-2",
                                ),

                                 dbc.Col(
                                    [dbc.Button(
                                        "About Graph",
                                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                                        color="secondary",
                                        size="sm",
                                    ), ],
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
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
    title = f"Top {k} Contributors by {action_type}"
    return title

# callback to update dropdown menu with user-inputted keywords
@callback(
    Output(f"patterns-{PAGE}-{VIZ_ID}", "options"),
    Output(f"keyword-{PAGE}-{VIZ_ID}", "data"),
    Input(f"patterns-{PAGE}-{VIZ_ID}", "search_value"),
    State(f"patterns-{PAGE}-{VIZ_ID}", "options"),
    State(f"keyword-{PAGE}-{VIZ_ID}", "data"),
    prevent_initial_call=True
)

def dropdown_menu(key, options, previous_key):
    """
    Adapted from https://community.plotly.com/t/allow-user-to-create-new-options-in-dcc-dropdown/8408/6
    The list of options for patterns to look for in contributor logins is updated at every key stroke.
    Suppose 'github' is added as an option. By default the list of options is updated to [gi, git, gith, githu, github].
    In order to prevent redundancy, the list of options and the user-inputted keyword is updated such that
    only the final keyword, 'github' is added to the list of options.

    :param key: A String representing the current key that the user has inputted into dcc.Dropdown
    :param options: A list of Strings with patterns to filter out contributors by in their login
    :param previous_key: A String representing the previous key that the user has inputted into dcc.Dropdown
    
    returns updated list of options and new keyword 
    """
    n = len(key)
    try:
        n_previous = len(previous_key)
    except:
        pass

    if previous_key is None and n > 0:
        # initialize the keyword by adding first key pressed to options
        options += [{'label': key, 'value': key}] 
    elif n > n_previous and n_previous > 0:
        # if more keys are pressed, remove the previous key and update option with the current key
        options = options[:-1] + [{'label': key, 'value': key}]
    elif n < n_previous and n_previous > 0:
        # if the current key / keyword is less than the previous key / keyword
        if n > 0:
            # if more keys are pressed, remove the previous key and update option with the current key
            options = options[:-1] + [{'label': key, 'value': key}]
        else:
            # if no keys are pressed, do not update options
            if n < n_previous - 1:
                key = None 
            else:
                # if user deletes all inputs, remove all options
                options = options[:-1]
    return options, key

# callback for contrib-importance graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"action-type-{PAGE}-{VIZ_ID}", "value"),
        Input(f"patterns-{PAGE}-{VIZ_ID}", "value"),
        Input(f"top-k-contributors-{PAGE}-{VIZ_ID}", "value"),

    ],
    background=True,
)

def create_top_k_cntrbs_graph(repolist, action_type, patterns, top_k):
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
    df = process_data(df, action_type, patterns, top_k)

    fig = create_figure(df, action_type)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False

def process_data(df: pd.DataFrame, action_type, patterns, top_k):
    # subset the df such that it only contains rows where the Action column value is the action type
    df = df[df["Action"].str.contains(action_type)]

    # option to filter out potential bots
    if patterns:
        # remove rows where login column value contains any keyword in patterns
        mask = df['login'].str.contains("|".join(patterns), na=False)
        df = df[~mask]

    # count the number of contributions for each contributor
    df = (df.groupby('cntrb_id')['Action'].count()).to_frame()

    # sort rows according to amount of contributions from greatest to least
    df.sort_values(by='cntrb_id', ascending=False, inplace=True)
    df = df.reset_index()

    # rename Action column to action_type
    df = df.rename(columns={'Action': action_type})

    # get the number of total contributions 
    t_sum = df[action_type].sum()

    # index df to get first k rows
    df = df.head(top_k)

    # convert cntrb_id from type UUID to String
    df['cntrb_id'] = df['cntrb_id'].apply(lambda x: str(x).split('-')[0])

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
        color_discrete_sequence=color_seq
        )
    
    # display percent contributions and cntrb_id in each wedge
    # format hover template to display cntrb_id and the number of their contributions according to the action_type
    fig.update_traces(
        textinfo='percent+label',
        textposition='inside',
        hovertemplate='Contributor ID: %{label} <br>Contributions: %{value}<br><extra></extra>')
    
    # add legend title
    fig.update_layout(
        legend_title_text = "Contributor ID"
    )
    
    return fig