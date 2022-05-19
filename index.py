from dash import html, callback_context, callback
from dash.dependencies import Input, Output, State
import dash
from dash import dcc
import plotly.express as px
from json import dumps
import numpy as np
import dash_bootstrap_components as dbc
import pandas as pd
import sqlalchemy as salc
from app import app, augur_db
import os

# import page files from project.
from pages import start, overview, cicd, chaoss
import query_callbacks


# generate entries for search bar
pr_query = f"""SELECT * FROM augur_data.explorer_entry_list"""

df_search_bar = augur_db.run_query(pr_query)

entries = np.concatenate(
    (df_search_bar.rg_name.unique(), df_search_bar.repo_git.unique()), axis=None
)
entries = entries.tolist()

# side bar code for page navigation
sidebar = html.Div(
    [
        html.H2("Pages", className="display-10"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Overview Page", href="/overview", active="exact"),
                dbc.NavLink("CI/CD Page", href="/cicd", active="exact"),
                dbc.NavLink("Chaoss Page", href="/chaoss", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ]
)


index_layout = dbc.Container(
    [
        # componets to store data from queries
        dcc.Store(id="repo_choices", storage_type="session", data=[]),
        dcc.Store(id="commits-data", data=[], storage_type="memory"),
        dcc.Store(id="contributions", data=[], storage_type="memory"),
        dcc.Store(id="issues-data", data=[], storage_type="memory"),
        dcc.Location(id="url"),
        dbc.Row(
            [
                dbc.Col(sidebar, width=1),
                dbc.Col(
                    [
                        html.H1(
                            "Sandiego Explorer Demo Multipage", className="text-center"
                        ),
                        # search bar with buttons
                        html.Label(
                            ["Select Github repos or orgs:"],
                            style={"font-weight": "bold"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id="projects",
                                            multi=True,
                                            value=["agroal"],
                                            options=[
                                                {"label": x, "value": x}
                                                for x in sorted(entries)
                                            ],
                                        )
                                    ],
                                    style={
                                        "width": "50%",
                                        "display": "table-cell",
                                        "verticalAlign": "middle",
                                        "padding-right": "10px",
                                    },
                                ),
                                dbc.Button(
                                    "Search",
                                    id="search",
                                    n_clicks=0,
                                    class_name="btn btn-primary",
                                    style={
                                        "verticalAlign": "top",
                                        "display": "table-cell",
                                    },
                                ),
                            ],
                            style={
                                "align": "right",
                                "display": "table",
                                "width": "60%",
                            },
                        ),
                        html.Div(id="results-output-container", className="mb-4"),
                        html.Div(id="display-page", children=[]),
                    ],
                    width={"size": 11, "offset": 0},
                ),
            ],
            justify="start",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Footer(
                            "Report issues to jkunstle@redhat.com, topic: Explorer Issue",
                            style={"textDecoration": "underline"},
                        )
                    ],
                    width={"offset": 9},
                )
            ],
        ),
    ],
    fluid=True,
    style={"padding-top": "1em"},
)

app.layout = index_layout

### Assemble all layouts ###
app.validation_layout = html.Div(
    children=[index_layout, start.layout, overview.layout, cicd.layout, chaoss.layout]
)

"""
    Page Callbacks- all query callbacks are in query_callbacks.py
"""

# page selection call back
@callback(Output("display-page", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/overview":
        return overview.layout
    elif pathname == "/cicd":
        return cicd.layout
    elif pathname == "/chaoss":
        return chaoss.layout
    elif pathname == "/":
        return start.layout
    else:
        return "404"


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
