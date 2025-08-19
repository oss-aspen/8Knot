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
from queries.contributor_funnel_query import contributor_funnel_query as cfq
import cache_manager.cache_facade as cf

PAGE = "contributors"
VIZ_ID = "contributor-funnel"

# Card for the Funnel Chart
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

# Card for the Drop-off Chart
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

# callback for funnel graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}-funnel", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}-funnel", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}-funnel", "is_open")],
)
def toggle_funnel_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for dropoff graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}-dropoff", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}-dropoff", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}-dropoff", "is_open")],
)
def toggle_dropoff_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for contributor funnel and dropoff graphs
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

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=cfq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    logging.warning(f"{VIZ_ID} - START")
    start = time.perf_counter()

    # GET ALL DATA FROM POSTGRES CACHE
    df_counts = cf.retrieve_from_cache(
        tablename=cfq.__name__,
        repolist=repolist,
    )

    # test if there is data
    if df_counts is None or df_counts.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph(), nodata_graph()

    # function for all data pre processing
    df_funnel, df_dropoff = process_data(df_counts)

    funnel_fig = create_funnel_figure(df_funnel)
    dropoff_fig = create_dropoff_figure(df_dropoff)
    
    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return funnel_fig, dropoff_fig


def process_data(df_counts: pd.DataFrame):
    """Process the funnel data and create separate dataframes for funnel and dropoff charts."""
    counts = df_counts.iloc[0].to_dict()
    stages = list(counts.keys())
    values = list(counts.values())

    # Data for funnel chart
    df_funnel = pd.DataFrame({
        'Stage': stages,
        'Count': values
    })

    # Data for drop-off chart
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
