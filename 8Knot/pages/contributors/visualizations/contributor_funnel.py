import logging
from textwrap import dedent

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
def nodata_graph(text="No data for this selection"):
    return {
        "layout": { "xaxis": {"visible": False}, "yaxis": {"visible": false}, "annotations": [{"text": text, "showarrow": False, "font": {"size": 20}}] }
    }

def execute_sql_query(query_string, params):
    print("--- MOCKING DATABASE QUERY ---")
    print(query_string)
    mock_data = {
        'All New Contributors': [1250],
        'Basic Engagement': [700],
        'Deeper Engagement': [250]
    }
    return pd.DataFrame(mock_data)

PAGE = "contributors"
VIZ_ID = "contributor-funnel"

gc_contributor_funnel = dbc.Card(
    [
        dbc.CardHeader(html.H3("Contributor Engagement Funnel", className="card-title", style={"textAlign": "center"})),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(dcc.Graph(id=f"{PAGE}-{VIZ_ID}-funnel-graph")),
                            width=12,
                            lg=6
                        ),
                        dbc.Col(
                            dcc.Loading(dcc.Graph(id=f"{PAGE}-{VIZ_ID}-dropoff-graph")),
                            width=12,
                            lg=6
                        )
                    ],
                    align="center"
                )
            ]
        ),
        dbc.CardFooter(
            "This visualization shows the journey of new contributors through different stages of engagement."
        )
    ],
)

@callback(
    Output(f"{PAGE}-{VIZ_ID}-funnel-graph", "figure"),
    Output(f"{PAGE}-{VIZ_ID}-dropoff-graph", "figure"),
    Input("repo-choices", "data"),
)
def create_funnel_and_dropoff_charts(repolist):
    if not repolist:
        raise PreventUpdate

    query = dedent(f"""
        WITH
          stage0_new AS (
            SELECT COUNT(DISTINCT cntrb_id) AS total_contributors
            FROM augur_data.augur_new_contributors
            -- If you filter by repo, add: WHERE repo_id = ANY(%(repo_ids)s)
          ),
          stage1_basic AS (
            SELECT COUNT(DISTINCT cntrb_id) AS engaged_contributors
            FROM augur_data.d1_contributor_engagement
            -- If you filter by repo, add: WHERE repo_id = ANY(%(repo_ids)s)
          ),
          stage2_deep AS (
            SELECT COUNT(DISTINCT cntrb_id) AS deeply_engaged_contributors
            FROM augur_data.d2_contributor_engagement
            -- If you filter by repo, add: WHERE repo_id = ANY(%(repo_ids)s)
          )
        SELECT
          (SELECT total_contributors FROM stage0_new) AS "All New Contributors",
          (SELECT engaged_contributors FROM stage1_basic) AS "Basic Engagement",
          (SELECT deeply_engaged_contributors FROM stage2_deep) AS "Deeper Engagement";
    """)
    
    try:
        df_counts = execute_sql_query(query, params={'repo_ids': repolist})
        if df_counts.empty:
            return nodata_graph(), nodata_graph()
    except Exception as e:
        logging.error(f"Error fetching funnel data: {e}")
        return nodata_graph("Error connecting to database"), nodata_graph("Error connecting to database")

    counts = df_counts.iloc[0].to_dict()
    stages = list(counts.keys())
    values = list(counts.values())

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

    funnel_fig = px.funnel(
        df_funnel,
        x='Count',
        y='Stage',
        title='Contributor Funnel',
        labels={'Count': 'Number of Contributors'}
    )
    funnel_fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))

    dropoff_fig = px.bar(
        df_dropoff,
        x='Drop-off Count',
        y='Transition',
        orientation='h',
        title='Drop-offs Between Stages',
        text='Drop-off Count', 
    )
    dropoff_fig.update_layout(
        yaxis_title=None,
        xaxis_title="Number of Dropped Contributors",
        margin=dict(l=40, r=40, t=40, b=40)
    )
    dropoff_fig.update_traces(textposition='outside')

    return funnel_fig, dropoff_fig

if __name__ == '__main__':
    app_instance = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
    
    app_instance.layout = dbc.Container([
        dcc.Store(id='repo-choices', data=['repo1', 'repo2']),
        gc_contributor_funnel
    ], fluid=True)
    
    app_instance.run_server(debug=True, port=8053)