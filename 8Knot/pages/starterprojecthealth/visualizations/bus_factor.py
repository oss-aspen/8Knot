from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import logging
import time
import datetime as dt
from pages.utils.graph_utils import color_seq
from queries.contributors_query import contributors_query as ctq
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import app

# Constants for the page and visualization ID
PAGE = "chaoss"
VIZ_ID = "bus-factor"

# Card layout for the Bus Factor visualization
gc_bus_factor = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Bus Factor",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                # Popover for graph information
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This graph displays the Bus Factor for the given Repository."
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                # Loading component for the graph
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


# Callback to toggle the popover for graph information
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

# Callback for generating the Bus Factor graph
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
        Input("bot-switch", "value"),
    ],
    background=True,
)
def create_top_k_cntrbs_graph(repolist, action_type, top_k, patterns, start_date, end_date, bot_switch):
    # Data retrieval and processing
    cache = cm()
    df = cache.grabm(func=ctq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=ctq, repos=repolist)

    # Log start of data processing
    logging.warning(f"{VIZ_ID}- START")

    # Check for data availability
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    # Filter data based on action type
    if not df["Action"].str.contains(action_type).any():
        return dash.no_update, True

    # Remove bot data if necessary
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # Process the data for the graph
    df = process_data(df, action_type, top_k, patterns, start_date, end_date)

    # Calculate the Bus Factor
    bus_factor = calculate_bus_factor(df, action_type)

    # Create and return the figure for the graph
    fig = create_figure(df, action_type, bus_factor)

    logging.warning(f"{VIZ_ID} - END")
    return fig, False

# Function to process data for the graph
def process_data(df: pd.DataFrame, action_type, top_k, patterns, start_date, end_date):
    # Convert 'created_at' to datetime and sort
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df = df.sort_values(by="created_at", ascending=True)

    # Apply filters based on date range and patterns
    if start_date is not None:
        df = df[df.created_at >= start_date]
    if end_date is not None:
        df = df[df.created_at <= end_date]
    df = df[df["Action"].str.contains(action_type)]
    if patterns:
        patterns_mask = df["login"].str.contains("|".join(patterns), na=False)
        df = df[~patterns_mask]

    # Group by contributor and count actions
    df = (df.groupby("cntrb_id")["Action"].count()).to_frame()
    df.sort_values(by="cntrb_id", ascending=False, inplace=True)
    df = df.reset_index()
    df = df.rename(columns={"Action": action_type})

    # Calculate total and top K contributions
    t_sum = df[action_type].sum()
    df = df.head(top_k)
    df["cntrb_id"] = df["cntrb_id"].apply(lambda x: str(x).split("-")[0])
    df_sum = df[action_type].sum()

    # Append the 'Other' category for remaining contributions
    df = df.append({"cntrb_id": "Other", action_type: t_sum - df_sum}, ignore_index=True)
    return df

# Function to calculate the Bus Factor
def calculate_bus_factor(df, action_type):
    total_contributions = df[action_type].sum()
    df['cumulative_percent'] = df[action_type].cumsum() / total_contributions
    return df[df['cumulative_percent'] <= 0.75].shape[0]

# Function to create the figure for the graph
def create_figure(df: pd.DataFrame, action_type, bus_factor):
    # Create a bar chart to represent the Bus Factor
    fig = px.bar(
        df,
        x='cntrb_id',
        y=action_type,
        title=f"Bus Factor: {bus_factor} (Top Contributors Highlighted)",
        labels={'cntrb_id': 'Contributor ID', action_type: 'Number of Contributions'}
    )
    # Add a horizontal line to highlight the Bus Factor threshold
    fig.add_hline(y=df[action_type].iloc[bus_factor - 1], line_dash="dot",
                  annotation_text="Bus Factor Threshold",
                  annotation_position="bottom right")
    # Update layout to remove legend
    fig.update_layout(showlegend=False)
    return fig
