from dash import html, dcc, Input, Output, State, callback
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import warnings

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
                                        dbc.Button("Send", id="send-btn", color="primary", n_clicks=0),
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
                dcc.Graph(id="ui-graph"),
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
    Output("ui-graph", "figure"),
    Input("send-btn", "n_clicks"),
    State("user-input", "value"),
    prevent_initial_call=True,
)
def update_response(n_clicks: int, message: str):
    """Respond to the latest user message and generate a simple random graph."""
    if not message:
        return "", go.Figure()

    # 🔗 TODO: Replace with your AI backend call
    ai_reply = f"You said: {message}"  # placeholder response

    # 📈 Generate a random line chart for demonstration
    x = np.arange(0, 10, 1)
    y = np.random.randint(0, 10, size=10)
    fig = go.Figure(data=go.Scatter(x=x, y=y, mode="lines+markers"))
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), title="Generative UI Graph")

    return html.P(ai_reply), fig