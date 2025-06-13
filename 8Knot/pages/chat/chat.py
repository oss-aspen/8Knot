from dash import html, dcc, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import warnings
from dotenv import load_dotenv
import os
from llama_stack_client import LlamaStackClient
import json
import re
import requests
from pymilvus import MilvusClient
import logging

# Repo Overview visualizations
from ..repo_overview.visualizations.code_languages import gc_code_language
from ..repo_overview.visualizations.ossf_scorecard import gc_ossf_scorecard
from ..repo_overview.visualizations.package_version import gc_package_version
from ..repo_overview.visualizations.repo_general_info import gc_repo_general_info

# Contributions visualizations
from ..contributions.visualizations.commits_over_time import gc_commits_over_time
from ..contributions.visualizations.issues_over_time import gc_issues_over_time
from ..contributions.visualizations.issue_staleness import gc_issue_staleness
from ..contributions.visualizations.pr_staleness import gc_pr_staleness
from ..contributions.visualizations.pr_over_time import gc_pr_over_time
from ..contributions.visualizations.cntrib_issue_assignment import gc_cntrib_issue_assignment
from ..contributions.visualizations.issue_assignment import gc_issue_assignment
from ..contributions.visualizations.pr_assignment import gc_pr_assignment
from ..contributions.visualizations.cntrb_pr_assignment import gc_cntrib_pr_assignment
from ..contributions.visualizations.pr_first_response import gc_pr_first_response
from ..contributions.visualizations.pr_review_response import gc_pr_review_response

# Contributors visualizations
from ..contributors.visualizations.contrib_drive_repeat import gc_contrib_drive_repeat
from ..contributors.visualizations.first_time_contributions import gc_first_time_contributions
from ..contributors.visualizations.contributors_types_over_time import gc_contributors_over_time
from ..contributors.visualizations.active_drifting_contributors import gc_active_drifting_contributors
from ..contributors.visualizations.new_contributor import gc_new_contributor
from ..contributors.visualizations.contrib_activity_cycle import gc_contrib_activity_cycle
from ..contributors.visualizations.contribs_by_action import gc_contribs_by_action
from ..contributors.visualizations.contrib_importance_pie import gc_contrib_importance_pie
from ..contributors.visualizations.contrib_importance_over_time import gc_lottery_factor_over_time

# CHAOSS metrics visualizations
from ..chaoss.visualizations.contrib_importance_pie import gc_contrib_importance_pie
from ..chaoss.visualizations.project_velocity import gc_project_velocity

# Codebase Visualizations
from ..codebase.visualizations.cntrb_file_heatmap import gc_cntrb_file_heatmap
from ..codebase.visualizations.contribution_file_heatmap import gc_contribution_file_heatmap
from ..codebase.visualizations.reviewer_file_heatmap import gc_reviewer_file_heatmap

# Affiliations Visualizations
from ..affiliation.visualizations.commit_domains import gc_commit_domains
from ..affiliation.visualizations.gh_org_affiliation import gc_gh_org_affiliation
from ..affiliation.visualizations.org_associated_activity import gc_org_associated_activity
from ..affiliation.visualizations.org_core_contributors import gc_org_core_contributors
from ..affiliation.visualizations.unqiue_domains import gc_unique_domains

m_client = MilvusClient("milvus_demo.db")
load_dotenv()

def calculate_embedding(text: str) -> list:
    """
    Calculate the embedding for a given text using the Nomic API.
    """

    url = f"{os.getenv('NOMIC_URL')}"

    headers = {"Authorization": f"Bearer {os.getenv('NOMIC_API_KEY')}"}

    payload = {
        "encoding_format" : "float",
        "input": text,
        "model": "/mnt/models/",
        "user" : "null"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        raise Exception(f"Error calculating embedding: {response.text}")

def find_similar_graphs(query: str, top_k: int = 5, score_threshold: float = None):
    embedding = calculate_embedding(query)
    results = m_client.search(
        collection_name="demo_collection",
        anns_field="vector",           # Name of the vector field
        data=[embedding],              # List of query vectors
        limit=top_k,
        search_params={"metric_type": "COSINE"},  # or "L2" or "COSINE" as appropriate
        output_fields=["title", "about", "identifier"],  # Fields to return in the results
    )
    logging.info(f"Search results: {results}")
    
    # Optionally filter by score threshold
    if score_threshold is not None:
        results = [r for r in results[0] if r.score >= score_threshold]
    else:
        results = results[0]
    return results



# Initialize LlamaStack client. We're shelving this code for now

# llama_url = os.getenv("LLAMA_HOST")
# client = LlamaStackClient(base_url=f"http://{llama_url}:8321")

# models = client.models.list()
# print(models)

# model_id = None

# for model in models:
#     if model.identifier == "qwen3:0.6b":
#         print("Found model qwen3:0.6b")
#         model_id = model.identifier
#         break

# print(model_id)

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/chat")

# ---------------------------
# Layout
# ---------------------------
layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H3("Chat with 8knot"),
                width={"size": 6, "offset": 3},
                className="text-center my-3",
            )
        ),
        # 💬 Chat card
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id="user-input",
                                            placeholder="Type your message…",
                                            type="text",
                                            autoComplete="off",
                                        ),
                                    ]
                                ),
                                html.Div(id="ai-response", className="mt-3"),
                            ]
                        )
                    ],
                    style={"width": "100%"},
                ),
                width={"size": 6, "offset": 3},
            )
        ),
        # 📈 Generative graph directly below chat card
        dbc.Row(
            dbc.Col(
                html.Div(id="ui-graph", style={"width": "100%"}),
                width={"size": 6, "offset": 3},
            )
        ),
    ],
    fluid=True,
)

# ---------------------------
# Callback – replace response & generate a new graph each send
# ---------------------------

@callback(
    Output("ai-response", "children"),
    Output("ui-graph", "children", allow_duplicate=True),
    Input("user-input", "n_submit"),
    State("user-input", "value"),
    prevent_initial_call=True,
)
def update_response(n_clicks: int, message: str):
    # If there's no message, return empty response
    if not message:
        return "", go.Figure()

    graphs = find_similar_graphs(message, top_k=5)
    card_components = []
    ai_reply = " "
    for graph in graphs:
        graph_id = graph.get("identifier")
        logging.info(f"Graph ID: {graph_id}")
        card_components.append(globals().get(f"{graph_id}"))
    return html.P(str(ai_reply)), html.Div(card_components)