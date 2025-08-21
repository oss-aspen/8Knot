from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import logging
import plotly.express as px
from dash.exceptions import PreventUpdate
import time

from pages.utils.job_utils import nodata_graph
from queries.contributor_funnel_query import contributor_engagement_query as ceq
import cache_manager.cache_facade as cf

PAGE = "contributors"
VIZ_ID = "contributor-funnel"

gc_contributor_funnel = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor Funnel",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This funnel chart shows the progression of contributors through different engagement stages, from initial interest to active contribution."
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}-funnel",
                    target=f"popover-target-{PAGE}-{VIZ_ID}-funnel",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}-funnel-graph"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"popover-target-{PAGE}-{VIZ_ID}-funnel",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    className="ms-auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
)

gc_contributor_dropoff = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Drop-offs Between Stages",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "This bar chart shows the number of contributors who drop off between each stage of the contributor funnel."
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}-dropoff",
                    target=f"popover-target-{PAGE}-{VIZ_ID}-dropoff",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}-dropoff-graph"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"popover-target-{PAGE}-{VIZ_ID}-dropoff",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    className="ms-auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
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


@callback(
    Output(f"{PAGE}-{VIZ_ID}-funnel-graph", "figure"),
    Output(f"{PAGE}-{VIZ_ID}-dropoff-graph", "figure"),
    [
        Input("repo-choices", "data"),
    ],
    background=True,
)
def create_funnel_and_dropoff_charts(repolist):
    if not repolist:
        raise PreventUpdate

    func_name = ceq.__name__
    not_cached = cf.get_uncached(func_name=func_name, repolist=repolist)
    if not_cached:
        logging.warning(f"{VIZ_ID}: Engagement data for {len(not_cached)} repos not cached. Dispatching worker.")
        ceq.apply_async(args=[not_cached])
        timeout = 180
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not cf.get_uncached(func_name=func_name, repolist=not_cached):
                break
            time.sleep(2)
        
        if cf.get_uncached(func_name=func_name, repolist=repolist):
            logging.warning(f"{VIZ_ID} - TIMEOUT WAITING FOR DATA")
            return nodata_graph, nodata_graph

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    df_engagement = cf.retrieve_from_cache(
        tablename=ceq.__name__,
        repolist=repolist,
    )

    if df_engagement is None or df_engagement.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, nodata_graph

    df_funnel, df_dropoff = process_data(df_engagement)

    funnel_fig = create_funnel_figure(df_funnel)
    dropoff_fig = create_dropoff_figure(df_dropoff)
    
    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return funnel_fig, dropoff_fig


def process_data(df: pd.DataFrame):
    """
    Process the raw engagement data to calculate funnel stages.
    This function now replicates the logic from the original SQL query.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    all_contributors_count = df['cntrb_id'].nunique()

    basic_mask = (
        df['d1_first_issue_created_at'].notna() |
        df['d1_first_pr_opened_at'].notna() |
        df['d1_first_pr_commented_at'].notna()
    )
    basic_contributors_count = df[basic_mask]['cntrb_id'].nunique()

    deep_mask = (
        (df['d2_has_merged_pr'] == True) |
        (df['d2_created_many_issues'] == True) |
        (df['d2_total_comments'] >= 5) |
        (df['d2_has_pr_with_many_commits'] == True) |
        (df['d2_commented_on_multiple_prs'] == True)
    )
    deep_contributors_count = df[deep_mask]['cntrb_id'].nunique()

    stages = ["All Contributors", "Basic Engagement", "Deep Engagement"]
    values = [all_contributors_count, basic_contributors_count, deep_contributors_count]
    
    df_funnel = pd.DataFrame({
        'Stage': stages,
        'Count': values
    })

    dropoff_stages = []
    dropoff_counts = []
    for i in range(len(values) - 1):
        dropoff_stages.append(f"{stages[i]} → {stages[i+1]}")
        dropoff_counts.append(values[i] - values[i+1])

    df_dropoff = pd.DataFrame({
        'Transition': dropoff_stages,
        'Drop-off Count': dropoff_counts
    })

    return df_funnel, df_dropoff


def create_funnel_figure(df_funnel: pd.DataFrame):
    """Create the funnel chart figure."""
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