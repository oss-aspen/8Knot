import logging
import time
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import dcc, html, callback
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

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
                html.H4("Contributor Funnel", className="card-title text-center"),
                dcc.Loading(dcc.Graph(id=f"{PAGE}-{VIZ_ID}-funnel-graph")),
            ]
        ),
    ],
)

# Card for the Drop-off Chart
gc_contributor_dropoff = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("Drop-offs Between Stages", className="card-title text-center"),
                dcc.Loading(dcc.Graph(id=f"{PAGE}-{VIZ_ID}-dropoff-graph")),
            ]
        ),
    ],
)

@callback(
    Output(f"{PAGE}-{VIZ_ID}-funnel-graph", "figure"),
    Output(f"{PAGE}-{VIZ_ID}-dropoff-graph", "figure"),
    Input("repo-choices", "data"),
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

    if df_counts is None or df_counts.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph(), nodata_graph()

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

    # Create funnel chart
    funnel_fig = px.funnel(
        df_funnel,
        x='Count',
        y='Stage',
        labels={'Count': 'Number of Contributors'}
    )
    funnel_fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))

    # Create drop-off bar chart
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
        margin=dict(l=40, r=40, t=40, b=40)
    )
    dropoff_fig.update_traces(textposition='outside')
    
    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return funnel_fig, dropoff_fig
