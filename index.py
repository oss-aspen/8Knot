from dash import html, callback_context
from dash.dependencies import Input, Output
import plotly.express as px
from json import dumps

from app import app
from app import server

# import page files from project.
from pages import start, overview, cicd


app.layout = html.Div(children=[
    html.H1(children="Sandiego Explorer Demo Multipage"),
    html.H3(children="Report issues to jkunstle@redhat.com, topic: Explorer Issue"),
    html.Div(children=[
        html.Button("Start Page", id="start-page", n_clicks=0),
        html.Button("Overview Page", id="overview-page", n_clicks=0),
        html.Button("CI/CD Page", id="cicd-page", n_clicks=0)
    ]),
    html.Div(id='display-page')
])

"""
    Page Callbacks
"""
@app.callback(
    Output('display-page', 'children'),
    Input('start-page', 'n_clicks'),
    Input('overview-page', 'n_clicks'),
    Input('cicd-page', 'n_clicks')
)
def return_template(_start, _overview, _cicd):
    ctx = callback_context
    caller = ctx.triggered[0]["prop_id"]

    # default caller on first execution.
    if caller == ".":
        return start.layout
    else:
        call_name = caller.split(".")[0]
        name_dict = {
            "start-page": start.layout,
            "overview-page": overview.layout,
            "cicd-page": cicd.layout
        }
        return name_dict[call_name]


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
