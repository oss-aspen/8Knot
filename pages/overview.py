from dash import html
from dash.dependencies import Input, Output

from app import app

layout = html.Div(children=[
    html.H1(children="Overview Page!"),
    html.Button("Press for Text!", id='this-button', n_clicks=0),
    html.Div(id='test-callback', children=[])
])

@app.callback(
    Output('test-callback', 'children'),
    Input('this-button', 'n_clicks')
)
def respond(n_clicks):
    return f"Good response, n_clicks: {n_clicks}"