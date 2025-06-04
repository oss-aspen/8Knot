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

from ..repo_overview.visualizations.code_languages import gc_code_language
from ..repo_overview.visualizations.ossf_scorecard import gc_ossf_scorecard
from ..repo_overview.visualizations.package_version import gc_package_version
from ..repo_overview.visualizations.repo_general_info import gc_repo_general_info
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
from ..contributors.visualizations.contrib_drive_repeat import gc_contrib_drive_repeat
from ..contributors.visualizations.first_time_contributions import gc_first_time_contributions
from ..contributors.visualizations.contributors_types_over_time import gc_contributors_over_time
from ..contributors.visualizations.active_drifting_contributors import gc_active_drifting_contributors
from ..contributors.visualizations.new_contributor import gc_new_contributor
from ..contributors.visualizations.contrib_activity_cycle import gc_contrib_activity_cycle
from ..contributors.visualizations.contribs_by_action import gc_contribs_by_action
from ..contributors.visualizations.contrib_importance_pie import gc_contrib_importance_pie
from ..contributors.visualizations.contrib_importance_over_time import gc_lottery_factor_over_time

def load_and_combine(prompt_file: str, json_file: str) -> str:
    """
    Load a prompt from a text file and a JSON file, and combine them into a single string.
    """
    with open(prompt_file, 'r') as f:
        prompt_text = f.read()
    
    with open(json_file, 'r') as f:
        json_data = json.load(f)
    
    # Convert JSON data to a formatted string
    json_text = json.dumps(json_data, indent=2)
    
    return f"{json_text}\n\n{prompt_text}"

def extract_json_array(text: str) -> str:
    """
    Extract the first occurrence of a JSON-style array (e.g. "[0,1,2,3]") from the input string.
    """
    # This regex matches an opening bracket [, then one or more digits separated by commas,
    # followed by an optional trailing '..' pattern, and a closing bracket ].
    pattern = r'\[\s*\d+(?:\s*,\s*\d+)*(?:\s*,\s*\.\.)?\s*\]'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return ""

load_dotenv()
llama_url = os.getenv("LLAMA_HOST")
client = LlamaStackClient(base_url=f"http://{llama_url}:8321")

models = client.models.list()

llm = next(m for m in models if m.model_type == "llm")
model_id = llm.identifier
print(model_id)

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
                width={"size": 8, "offset": 2},
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
    """Respond to the latest user message and generate a simple random graph."""
    if not message:
        return "", go.Figure()

    response = client.inference.chat_completion(
            model_id=model_id,
            messages=[
                {"role": "system", "content": load_and_combine("prompt.txt", "graphs.json")},
                {"role": "user", "content": f"{message}"},
            ],
            stream=False
        )

    # card_components = [gc_package_version, gc_code_language, gc_active_drifting_contributors]
    card_components = []

    ai_reply = response.completion_message.content.strip()
    # actual_response = response.completion_message.content.strip()
    parsed_response = json.loads(extract_json_array(ai_reply))

    with open("graphs.json", "r") as f:
        graph_data = json.load(f)

    for number in parsed_response:
        card_components.append(globals().get(f"{graph_data[number]['id']}"))

    return html.P(ai_reply), html.Div(card_components)