from dash import html
from dash.dependencies import Input, Output

from app import app
import time

overview_layout = html.Div(children=[
    html.H1(children="Overview Page!"),
    html.Div(id='test-callback')
])

@app.callback(
    Output('test-response', 'children'),
    Input('test-callback', 'value')
)
def respond(val):
    print("in respond funcion")
    return f"Good response!"
