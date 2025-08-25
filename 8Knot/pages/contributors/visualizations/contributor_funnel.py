from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from datetime import date, timedelta
import pandas as pd
import logging
import plotly.express as px
from dash.exceptions import PreventUpdate
import time

from pages.utils.job_utils import nodata_graph
# CHANGED: Use the raw contributors_query instead of the pre-aggregated one
from queries.contributors_query import contributors_query as cnq
import cache_manager.cache_facade as cf
import app

PAGE = "contributors"
VIZ_ID = "contributor-funnel"

gc_contributor_funnel = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Contributor Funnel",
                                className="card-title",
                            ),
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}-funnel",
                                color="outline-secondary",
                                size="sm",
                                className="about-graph-button",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    justify="between",
                    className="mb-3",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This funnel chart shows the progression of contributors through different engagement stages, from initial interest to active contribution, within the selected time range."
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}-funnel",
                    target=f"popover-target-{PAGE}-{VIZ_ID}-funnel",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}-funnel-graph"),
                    style={"marginBottom": "1rem"},
                ),
                html.Hr(  # Divider between graph and controls
                    style={
                        "borderColor": "#909090",
                        "margin": "1.5rem -1.5rem",
                        "width": "calc(100% + 3rem)",
                    }
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Select Time Range:",
                                    html_for=f"date-picker-{PAGE}-{VIZ_ID}-funnel",
                                    width="auto",
                                ),
                                dbc.Col(
                                    dcc.DatePickerRange(
                                        id=f"date-picker-{PAGE}-{VIZ_ID}-funnel",
                                        min_date_allowed=date(2015, 1, 1),
                                        max_date_allowed=date.today(),
                                        start_date=date.today() - timedelta(days=365),
                                        end_date=date.today(),
                                        display_format='YYYY-MM-DD',
                                        className="dark-date-picker",
                                    ),
                                    width=5,
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ],
            style={"padding": "1.5rem"},
        ),
    ],
    className="dark-card",
)

gc_contributor_dropoff = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.H3(
                                "Drop-offs Between Stages",
                                className="card-title",
                            ),
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}-dropoff",
                                color="outline-secondary",
                                size="sm",
                                className="about-graph-button",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    justify="between",
                    className="mb-3",
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This bar chart shows the number of contributors who drop off between each stage of the contributor funnel for the selected time range."
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}-dropoff",
                    target=f"popover-target-{PAGE}-{VIZ_ID}-dropoff",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}-dropoff-graph"),
                    style={"marginBottom": "1rem"},
                ),
                # REMOVED: Redundant date picker controls for this graph. It will now sync with the funnel chart's date picker.
            ],
            style={"padding": "1.5rem"},
        ),
    ],
    className="dark-card",
)

@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}-funnel", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}-funnel", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}-funnel", "is_open")],
)
def toggle_funnel_popover(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}-dropoff", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}-dropoff", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}-dropoff", "is_open")],
)
def toggle_dropoff_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# UPDATED: Callback now uses a single date picker for both graphs
@callback(
    Output(f"{PAGE}-{VIZ_ID}-funnel-graph", "figure"),
    Output(f"{PAGE}-{VIZ_ID}-dropoff-graph", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"date-picker-{PAGE}-{VIZ_ID}-funnel", "start_date"),
        Input(f"date-picker-{PAGE}-{VIZ_ID}-funnel", "end_date"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def create_funnel_and_dropoff_charts(repolist, start_date, end_date, bot_switch):
    if not repolist:
        raise PreventUpdate

    # UPDATED: Using contributors_query (cnq) now
    func_name = cnq.__name__
    not_cached = cf.get_uncached(func_name=func_name, repolist=repolist)
    if not_cached:
        logging.warning(f"{VIZ_ID}: Engagement data for {len(not_cached)} repos not cached. Dispatching worker.")
        cnq.apply_async(args=[not_cached])
        timeout = 180
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not cf.get_uncached(func_name=func_name, repolist=not_cached):
                break
            time.sleep(2)

        if cf.get_uncached(func_name=func_name, repolist=repolist):
            logging.warning(f"{VIZ_ID} - TIMEOUT WAITING FOR DATA")
            return nodata_graph(), nodata_graph()

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # UPDATED: Retrieving raw action data from cache
    df_actions = cf.retrieve_from_cache(
        tablename=cnq.__name__,
        repolist=repolist,
    )

    if df_actions is None or df_actions.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph(), nodata_graph()

    # UPDATED: Call the new processing function once for both graphs
    df_funnel, df_dropoff = process_data(df_actions, start_date, end_date, bot_switch)

    if df_funnel.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE AFTER PROCESSING")
        return nodata_graph(), nodata_graph()

    funnel_fig = create_funnel_figure(df_funnel)
    dropoff_fig = create_dropoff_figure(df_dropoff)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return funnel_fig, dropoff_fig


# REWRITTEN: This function now processes the raw action data to build the funnel dynamically.
def process_data(df: pd.DataFrame, start_date, end_date, bot_switch):
    """
    Process the raw contributor action data to calculate funnel stages based on activity
    within the selected date range.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Convert to datetime and filter by date range
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    start_dt = pd.to_datetime(start_date, utc=True)
    end_dt = pd.to_datetime(end_date, utc=True)
    df_filtered = df[(df['created_at'] >= start_dt) & (df['created_at'] <= end_dt)]

    if df_filtered.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Apply bot filtering
    if bot_switch and "cntrb_id" in df_filtered.columns:
        df_filtered = df_filtered[~df_filtered["cntrb_id"].isin(app.bots_list)]

    # Define actions for each engagement level
    basic_actions = ['issue_opened', 'pull_request_open', 'pull_request_comment']
    deep_actions = ['pull_request_merged']

    # Get unique contributors who performed these actions within the time range
    basic_contributors = set(df_filtered[df_filtered['action'].isin(basic_actions)]['cntrb_id'].unique())
    deep_contributors_from_actions = set(df_filtered[df_filtered['action'].isin(deep_actions)]['cntrb_id'].unique())

    # The top of the funnel includes anyone who performed a basic or deep action.
    total_engaged_contributors = basic_contributors.union(deep_contributors_from_actions)

    # The bottom of the funnel are those from the top set who also performed a deep action.
    deeply_engaged_contributors = total_engaged_contributors.intersection(deep_contributors_from_actions)

    # Define funnel stages and values
    stages = ["Engaged Contributors", "Deeply Engaged (Merged PR)"]
    values = [len(total_engaged_contributors), len(deeply_engaged_contributors)]

    df_funnel = pd.DataFrame({'Stage': stages, 'Count': values})

    # Calculate drop-offs between stages
    dropoff_stages = []
    dropoff_counts = []
    if len(values) > 1:
        dropoff_stages.append(f"{stages[0]} → {stages[1]}")
        dropoff_counts.append(values[0] - values[1])

    df_dropoff = pd.DataFrame({'Transition': dropoff_stages, 'Drop-off Count': dropoff_counts})

    return df_funnel, df_dropoff


def create_funnel_figure(df_funnel: pd.DataFrame):
    """Create the funnel chart figure."""
    if df_funnel.empty:
        return nodata_graph()
    funnel_fig = px.funnel(
        df_funnel,
        x='Count',
        y='Stage',
        labels={'Count': 'Number of Contributors'}
    )
    funnel_fig.update_layout(
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(size=14)
    )
    return funnel_fig


def create_dropoff_figure(df_dropoff: pd.DataFrame):
    """Create the drop-off bar chart figure."""
    if df_dropoff.empty:
        return nodata_graph()
    dropoff_fig = px.bar(
        df_dropoff,
        x='Drop-off Count',
        y='Transition',
        orientation='h',
        text='Drop-off Count',
    )
    dropoff_fig.update_layout(
        yaxis_title=None,
        xaxis_title="Number of Dropped Contributors",
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(size=14)
    )
    dropoff_fig.update_traces(textposition='outside')
    return dropoff_fig
