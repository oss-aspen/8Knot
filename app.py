import dash
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output
import plotly.express as px

# import page files from project.
import pages.start as start_page
import pages.overview as overview_page
import pages.cicd as cicd_page

app = dash.Dash(__name__)

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

@app.callback(
    Output('display-page', 'children'),
    Input('start-page', 'n_clicks'),
    Input('overview-page', 'n_clicks'),
    Input('cicd-page', 'n_clicks')
)
def show_page(start, overview, cicd):
    """Output page requested by above button press. Function is callback.

    Args:
        start (int): Number of times button 'Start Page' has been clicked.
        overview (int): Number of times button 'Overview Page' has been clicked.
        cicd (int): Number of time button 'CI/CD Page has been clicked.

    Returns:
        html layout child of above Div to display page layout.

    Raises:
        None
    """

    changed_page: int = None

    """
        ref: https://dash.plotly.com/dash-html-components/button
    """
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if "start-page" in changed_id:
        changed_page = 0
    elif "overview-page" in changed_id:
        changed_page = 1
    elif "cicd-page" in changed_id:
        changed_page = 2
    else:
        changed_page = 0

    return build_layouts(changed_page)

def build_layouts(page_idx: int):
    """Output layout of all pages

    Args:
        page_idx (int): index of page to return.

    Returns:
        html.Div: layout for page

    Raises:
        None
    """
    if page_idx == 0:
        return start_page.start_layout
    if page_idx == 1:
        return overview_page.overview_layout
    if page_idx == 2:
        return cicd_page.cicd_layout

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)