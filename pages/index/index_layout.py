from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from app import augur
import os
import logging

# if param doesn't exist, default to False. Otherwise,
# use the param's booly value.
if os.getenv("AUGUR_LOGIN_ENABLED", "False") == "True":
    logging.debug("LOGIN ENABLED")
    login_navbar = [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.DropdownMenu(
                                    children=[
                                        dbc.DropdownMenuItem(
                                            "Refresh",
                                            id="refresh-button",
                                        ),
                                        dbc.DropdownMenuItem(
                                            "Log out",
                                            id="logout-button",
                                        ),
                                    ],
                                    nav=True,
                                    in_navbar=True,
                                    label="More",
                                    id="nav-dropdown",
                                ),
                            ),
                            dbc.Popover(
                                children="Login Failed",
                                body=True,
                                id="login-popover",
                                is_open=False,
                                placement="bottom-end",
                                target="nav-dropdown",
                            ),
                            html.Div(
                                id="nav-login-container",
                                children=[],
                            ),
                        ]
                    )
                )
            ],
            align="center",
        ),
    ]
else:
    logging.debug("LOGIN DISABLED")
    login_navbar = [html.Div()]

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Img(src=dash.get_asset_url("logo2.png"), height="40px"),
                            dbc.NavbarBrand(
                                "8Knot Community Data",
                                id="navbar-title",
                                className="ms-2",
                            ),
                        ],
                        width={"size": "auto"},
                    ),
                    dbc.Col(
                        [
                            dbc.Nav(
                                [
                                    dbc.NavLink(page["name"], href=page["path"], active="exact")
                                    for page in dash.page_registry.values()
                                    if page["module"] != "pages.not_found_404"
                                ],
                                navbar=True,
                            )
                        ],
                        width={"size": "auto"},
                    ),
                ],
                align="center",
                className="g-0",
                justify="start",
            ),
            # packaged as a list to make linter happy-
            # it keeps making the login_navpar page-wrap as a tuple,
            # so I wrapped it in a list.
            login_navbar[0],
        ],
        fluid=True,
    ),
    color="primary",
    dark=True,
    sticky="top",
)

navbar_bottom = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            dbc.NavLink(
                "Visualization request",
                href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=enhancement%2Cvisualization&template=visualizations.md",
                external_link="True",
                target="_blank",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Bug",
                href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=bug&template=bug_report.md",
                external_link="True",
                target="_blank",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Repo/Org Request",
                href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=augur&template=augur_load.md",
                external_link="True",
                target="_blank",
            )
        ),
    ],
    brand="",
    brand_href="#",
    color="primary",
    dark=True,
    fluid=True,
)

search_bar = html.Div(
    [
        html.Div(
            [
                dmc.MultiSelect(
                    id="projects",
                    searchable=True,
                    clearable=True,
                    nothingFound="No matching repos/orgs.",
                    variant="filled",
                    debounce=100,
                    data=[augur.initial_multiselect_option()],
                    value=[augur.initial_multiselect_option()["value"]],
                    style={"fontSize": 16},
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
                "paddingRight": "10px",
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
)

layout = dbc.Container(
    [
        # componets to store data from queries
        dcc.Store(id="repo-choices", storage_type="session", data=[]),
        # components to store job-ids for the worker queue
        dcc.Store(id="job-ids", storage_type="session", data=[]),
        dcc.Store(id="refresh-groups", storage_type="session", data=True),
        dcc.Store(id="augur_user_groups_dash_persistence", storage_type="session", data={}),
        dcc.Store(
            id="augur_user_group_options_dash_persistence",
            storage_type="session",
            data=[],
        ),
        dcc.Store(id="augur_user_bearer_token_dash_persistence", storage_type="local", data=""),
        dcc.Store(id="augur_username_dash_persistence", storage_type="local", data=""),
        dcc.Store(id="augur_refresh_token_dash_persistence", storage_type="local", data=""),
        dcc.Store(id="augur_token_expiration_dash_persistence", storage_type="local", data=""),
        dcc.Store(id="login-succeeded", data=True),
        dcc.Location(id="url"),
        navbar,
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Select Github repos or orgs:",
                            html_for="projects",
                            width="auto",
                            size="lg",
                        ),
                        search_bar,
                        dcc.Loading(
                            children=[html.Div(id="results-output-container", className="mb-4")],
                            color="#119DFF",
                            type="dot",
                            fullscreen=True,
                        ),
                        dcc.Loading(
                            dbc.Badge(
                                children="Data Loaded",
                                id="data-badge",
                                color="#436755",
                                className="me-1",
                            ),
                            type="cube",
                            color="#436755",
                        ),
                        # where our page will be rendered
                        dash.page_container,
                    ],
                ),
            ],
            justify="start",
        ),
        navbar_bottom,
    ],
    fluid=True,
    className="dbc",
)