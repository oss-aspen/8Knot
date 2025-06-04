from dash import html, dcc, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import warnings
from dotenv import load_dotenv
import os
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
from llama_stack_client import LlamaStackClient
import json

prompt_text = '''
**SYSTEM PROMPT**

You are a recommendation engine that helps select the most relevant visualizations for a user from a predefined list of charts. The user will describe their goal, interest, or question related to software repositories, open source communities, or codebase analytics. You must decide which visualizations from the provided list are most appropriate to help the user achieve their objective.
The JSON charts included above will include the name of the graph, some information about the graph, along with their ID.

**Your output must be a JSON array of indices** that point to the most relevant charts in the list. Each index corresponds to the position in the list (starting from 0).

Guidelines:

* Use the user's intent to determine which visualizations offer direct insight.
* Do not explain your reasoning or include any extra text.
* Return between 1–5 indices, prioritizing quality and relevance over quantity.
* Be precise: only choose visualizations directly useful for the user’s request.
* Consider whether the user is asking about:

  * Code language usage → suggest language distribution charts.
  * Dependency management → suggest package version insights.
  * Contributor behavior → suggest engagement, arrival, or retention charts.
  * Risk or reliance → suggest lottery/bus factor visualizations.
  * Activity patterns → suggest timing or action-type breakdown charts.

**Return only a JSON array of integers. Example:**

```json
[0, 2, 5]
```

If none are relevant, return an empty array:

```json
[]
```
Again, **Your output must be a JSON array of indices** that point to the most relevant charts in the list. Each index corresponds to the position in the list (starting from 0).

DO NOT INCLUDE ANY OTHER TEXT OR EXPLANATION. JUST THE JSON ARRAY OF INDICES.
'''
json_text = '''
[
    {
        "name" : "File Language By File",
        "about" : "Visualizes the percent of files or lines of code by language.",
        "id" : "gc_code_language"
    },
    {
        "name" : "Package Version Updates",
        "about" : "Visualizes for each packaged dependancy, if it is up to date and if not if it is less than 6 months out, between 6 months and a year, or greater than a year.",
        "id" : "gc_package_version"
    },
    {
        "name" : "Contributor Growth By Engagement",
        "about" : "Visualizes growth of contributor population, including sub-populations in consideration of how recently a contributor has contributed. Please see definitions of 'Contributor Recency' on Info page.",
        "id" : "gc_active_drifting_contributors"
    },
    {
        "name" : "Contributor Activity Cycle",
        "about" : "Visualizes the distribution of Commit timestamps by Weekday or Hour. Helps to describe operating-hours of community code contributions.",
        "id" : "gc_contrib_activity_cycle"
    }
]
'''


def load_and_combine(prompt_text: str, json_text: str) -> str:
    combined = f"List of Visualizations:\n{json_text.strip()}\n\n{prompt_text.strip()}"
    return combined

import re

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

    # # 🔗 TODO: Replace with your AI backend call
    # ai_reply = f"You said: {message}"  # placeholder response

    response = client.inference.chat_completion(
            model_id=model_id,
            messages=[
                {"role": "system", "content": load_and_combine(prompt_text, json_text)},
                {"role": "user", "content": f"{message}"},
            ],
            stream=False
        )

    # card_components = [gc_package_version, gc_code_language, gc_active_drifting_contributors]
    card_components = []

    ai_reply = response.completion_message.content.strip()
    # actual_response = response.completion_message.content.strip()
    parsed_response = json.loads(extract_json_array(ai_reply))
    graph_data = json.loads(json_text)

    # with open("graphs.json", "r") as f:
    #     graph_data = json.load(f)

    for number in parsed_response:
        card_components.append(globals().get(f"{graph_data[number]['id']}"))
    

    # if "graph_type" not in parsed_response:
    #     ai_reply = "I couldn't understand your request. Please try again."
    #     return html.P(ai_reply), go.Figure()
    # graph_type = parsed_response["graph_type"]
    # ai_reply = f"Generating graph for: {graph_type}"

    # if graph_type == "File-Language-By-File":
    #     card = gc_code_language
    # elif graph_type == "Package-Version-Updates":
    #     card = gc_package_version
    # else:
    #     card = gc_ossf_scorecard

    # # 📈 Generate a random line chart for demonstration
    # x = np.arange(0, 10, 1)
    # y = np.random.randint(0, 10, size=10)
    # fig = go.Figure(data=go.Scatter(x=x, y=y, mode="lines+markers"))
    # fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), title="Generative UI Graph")

    return html.P(ai_reply), html.Div(card_components)