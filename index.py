from dash import html, callback
from dash.dependencies import Input, Output
from dash import dcc
import dash
import dash_labs as dl
import dash_bootstrap_components as dbc
from app import app, entries

# import page files from project.
from pages import start, overview, cicd, chaoss
import query_callbacks


# side bar code for page navigation
sidebar = html.Div(
    [
        html.H2("Pages", className="display-10"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(page["name"], href=page["path"], active="exact")
                for page in dash.page_registry.values()
                if page["module"] != "pages.not_found_404"
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
                                                for x in entries
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
                        # where our page will be rendered
                        dl.plugins.page_container,
                    ],
                    width={"size": 11},
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

print("VALIDATE_LAYOUT - START")
app.layout = index_layout

### Assemble all layouts ###
app.validation_layout = html.Div(
    children=[index_layout, start.layout, overview.layout, cicd.layout, chaoss.layout]
)
print("VALIDATE_LAYOUT - END")


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
