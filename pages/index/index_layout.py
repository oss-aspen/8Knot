from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from app import augur

sidebar = html.Div(
    [
        html.H2("Pages", className="display-10"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(page["name"], href=page["path"])
                for page in dash.page_registry.values()
                if page["module"] != "pages.not_found_404"
            ],
            vertical=True,
            pills=True,
        ),
    ]
)

layout = dbc.Container(
    [
        # componets to store data from queries
        dcc.Store(id="repo-choices", storage_type="session", data=[]),
        # components to store job-ids for the worker queue
        dcc.Store(id="job-ids", storage_type="session", data=[]),
        dcc.Store(id="users_augur_groups", storage_type="memory", data=[]),
        dcc.Store(id="user_bearer_token", storage_type="session", data=""),
        dcc.Store(id="augur_username", storage_type="session", data=""),
        dcc.Location(id="url"),
        dbc.Row(
            [
                # from above definition
                dbc.Col(sidebar, width=1),
                dbc.Col(
                    [
                        html.H1("8Knot Community Data", className="text-center"),
                        # search bar with buttons
                        dbc.Label(
                            "Select Github repos or orgs:",
                            html_for="projects",
                            width="auto",
                            size="lg",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id="projects",
                                            multi=True,
                                            options=[augur.get_search_input()],
                                            value=[augur.get_search_input()],
                                            style={"font-size": 16},
                                        ),
                                        dbc.Alert(
                                            children='Please ensure that your spelling is correct. \
                                                If your selection definitely isn\'t present, please request that \
                                                it be loaded using the help button "REPO/ORG Request" \
                                                in the bottom right corner of the screen.',
                                            id="help-alert",
                                            dismissable=True,
                                            fade=True,
                                            is_open=False,
                                            color="info",
                                        ),
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
                                    size="md",
                                ),
                                dbc.Button(
                                    "Help",
                                    id="search-help",
                                    n_clicks=0,
                                    size="md",
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
                        dcc.Loading(
                            children=[
                                html.Div(
                                    id="results-output-container", className="mb-4"
                                )
                            ],
                            color="#119DFF",
                            type="dot",
                            fullscreen=True,
                        ),
                        dcc.Loading(
                            dbc.Badge(
                                children="Data Loaded",
                                id="data_badge",
                                color="#436755",
                                className="me-1",
                            ),
                            type="cube",
                            color="#436755",
                        ),
                        # where our page will be rendered
                        dash.page_container,
                    ],
                    width={"size": 9},
                ),
                dbc.Col(
                    [html.Div(id="login-container", children=[])], width={"size": 2}
                ),
            ],
            justify="start",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5(
                            "Have a bug or feature request?",
                            className="mb-2"
                            # style={"textDecoration": "underline"},
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Visualization request",
                                    color="primary",
                                    size="sm",
                                    className="me-1",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=enhancement%2Cvisualization&template=visualizations.md",
                                ),
                                dbc.Button(
                                    "Bug",
                                    color="primary",
                                    size="sm",
                                    className="me-1",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=bug&template=bug_report.md",
                                ),
                                dbc.Button(
                                    "Repo/Org Request",
                                    size="sm",
                                    color="primary",
                                    className="me-1",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=augur&template=augur_load.md",
                                ),
                            ]
                        ),
                    ],
                    width={"offset": 10},
                    style={"margin-bottom": ".5%"},
                )
            ],
        ),
    ],
    fluid=True,
    className="dbc",
    style={"padding-top": "1em"},
)
