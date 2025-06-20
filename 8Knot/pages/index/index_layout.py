from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from app import augur
import os
import logging
from dash.dependencies import Input, Output, State

#  login banner that will be displayed when login is disabled
login_banner = None
if os.getenv("AUGUR_LOGIN_ENABLED", "False") != "True":
    login_banner = html.Div(
        dbc.Alert(
            [
                html.H4(
                    "Login is Currently Disabled",
                    className="alert-heading",
                    style={"color": "black", "fontWeight": "600", "margin": "0 0 8px 0", "textShadow": "none"},
                ),
                html.P(
                    [
                        "If you need to collect data on new repositories, please ",
                        html.A(
                            "create a repository collection request",
                            href="https://github.com/oss-aspen/8Knot/issues/new?template=augur_load.md",
                            target="_blank",
                            style={"fontWeight": "500", "color": "#1565C0"},
                        ),
                        ".",
                    ],
                    style={"color": "#333333", "margin": "0 0 10px 0"},
                ),
            ],
            color="light",
            dismissable=True,
            id="login-disabled-banner",
            className="mb-0",
            style={
                "backgroundColor": "#EDF7ED",  # Light green background
                "borderColor": "#6b8976",  # Darker green border from palette
                "border": "1px solid #6b8976",
                "borderLeft": "5px solid #6b8976",
                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.15)",
                "maxWidth": "400px",
                "padding": "15px",
                "zIndex": "1000",
            },
        ),
        style={"position": "fixed", "top": "70px", "right": "20px", "zIndex": "1000"},  # Position below navbar
    )

# if param doesn't exist, default to False. Otherwise, use the param's value.
# this determines if the login option will be shown or not
if os.getenv("AUGUR_LOGIN_ENABLED", "False") == "True":
    logging.warning("LOGIN ENABLED")
    login_navbar = [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Nav(
                        [
                            dcc.Loading(
                                children=[
                                    html.Div(
                                        id="nav-login-container",
                                        children=[],
                                    ),
                                ]
                            ),
                            dbc.NavItem(
                                dbc.NavLink("Refresh Groups", id="refresh-button", disabled=True),
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    "Manage Groups",
                                    id="manage-group-button",
                                    disabled=True,
                                    href=f"{augur.user_account_endpoint}?section=tracker",
                                    external_link="True",
                                    target="_blank",
                                ),
                            ),
                            dbc.NavItem(
                                dbc.NavLink(
                                    "Log out",
                                    id="logout-button",
                                    disabled=True,
                                    href="/logout/",
                                    external_link=True,
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
                        ]
                    )
                )
            ],
            align="center",
        ),
    ]
else:
    logging.warning("LOGIN DISABLED")
    login_navbar = [html.Div()]

# navbar for top of screen
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Img(
                                src=dash.get_asset_url("8knot-logo-vertical.png"),
                                height="40px",
                            ),
                            dbc.NavbarBrand(
                                "8Knot",
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
                                    dbc.NavLink("Welcome", href="/", active="exact"),
                                    dbc.NavLink("Repo Overview", href="/repo_overview", active="exact"),
                                    dbc.NavLink(
                                        "Contributions",
                                        href="/contributions",
                                        active="exact",
                                    ),
                                    dbc.DropdownMenu(
                                        [
                                            dbc.DropdownMenuItem(
                                                "Behavior",
                                                href="/contributors/behavior",
                                            ),
                                            dbc.DropdownMenuItem(
                                                "Contribution Types",
                                                href="/contributors/contribution_types",
                                            ),
                                        ],
                                        label="Contributors",
                                        nav=True,
                                    ),
                                    dbc.NavLink(
                                        "Affiliation",
                                        href="/affiliation",
                                        active="exact",
                                    ),
                                    dbc.NavLink("CHAOSS", href="/chaoss", active="exact"),
                                    dbc.NavLink("Codebase", href="/codebase", active="exact"),
                                    dbc.NavLink("Info", href="/info", active="exact"),
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

search_bar = html.Div(
    [
        # Add client-side caching component
        dcc.Store(id="cached-options", storage_type="session"),
        # Hidden div to trigger cache initialization on page load
        html.Div(id="cache-init-trigger", style={"display": "none"}),
        # Storage quota warning
        dcc.Store(id="search-cache-init-hidden", storage_type="session"),
        # Warning alert for when browser storage quota is exceeded
        html.Div(
            dbc.Alert(
                [
                    html.I(className="quota-warning-icon"),  # Warning icon
                    "Browser storage limit reached. Search will use a reduced cache which may slightly impact performance. All features will still work normally.",
                ],
                id="storage-quota-warning",  # ID used by Javascript to show/hide this alert
                color="warning",
                dismissable=True,
                style={"display": "none"},  # Initially hidden, controlled by JavaScript
                className="mt-2 mb-0",
            ),
            className="search-bar-component",
        ),
        dbc.Stack(
            [
                html.Div(
                    [
                        dmc.MultiSelect(
                            id="projects",
                            searchable=True,
                            clearable=True,
                            nothingFound="No matching repos/orgs.",
                            variant="filled",
                            debounce=100,  # debounce time for the search input, since we're implementing client-side caching, we can use a faster debounce
                            data=[augur.initial_multiselect_option()],
                            value=[augur.initial_multiselect_option()["value"]],
                            style={"fontSize": 16},
                            maxDropdownHeight=300,  # limits the dropdown menu's height to 300px
                            zIndex=9999,  # ensures the dropdown menu is on top of other elements
                            dropdownPosition="bottom",  # forces the dropdown to open downwards
                            transitionDuration=150,  # transition duration for the dropdown menu
                            className="searchbar-dropdown",
                        ),
                        # Add search status indicator
                        html.Div(id="search-status", className="search-status-indicator", style={"display": "none"}),
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
                        dbc.Alert(
                            children="List of repos",
                            id="repo-list-alert",
                            dismissable=True,
                            fade=True,
                            is_open=False,
                            color="light",
                            # if number of repos is large, render as a scrolling window
                            style={"overflow-y": "scroll", "max-height": "440px"},
                        ),
                    ],
                    style={
                        "width": "100%",
                        "marginBottom": "16px",
                    },
                ),
                html.Div(
                    [
                        dbc.Button(
                            "Search",
                            id="search",
                            n_clicks=0,
                            size="md",
                            className="me-2 mb-2",
                        ),
                        dbc.Button(
                            "Help",
                            id="search-help",
                            n_clicks=0,
                            size="md",
                            className="me-2 mb-2",
                        ),
                        dbc.Button(
                            "Repo List",
                            id="repo-list-button",
                            n_clicks=0,
                            size="md",
                            className="mb-2",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexWrap": "wrap",
                        "marginBottom": "16px",
                    },
                ),
                html.Div(
                    [
                        dbc.Switch(
                            id="bot-switch",
                            label="GitHub Bot Filter",
                            value=True,
                            input_class_name="botlist-filter-switch",
                            style={"fontSize": 16},
                        ),
                    ],
                    style={
                        "marginTop": "8px",
                        "marginBottom": "16px",
                    },
                ),
            ],
            direction="vertical",
            style={
                "width": "100%",
            },
        ),
    ]
)

# Add a Store to keep sidebar state
sidebar_state_store = dcc.Store(id="sidebar-collapsed", data=False, storage_type="session")

layout = html.Div(
    [
        dcc.Store(id="repo-choices", storage_type="session", data=[]),
        dcc.Store(id="job-ids", storage_type="session", data=[]),
        dcc.Store(id="user-group-loading-signal", data="", storage_type="memory"),
        sidebar_state_store,
        dcc.Location(id="url"),
        html.Script(
            """
            window.addEventListener('error', function(event) {
                if (event.message && event.message.toLowerCase().includes('quota') &&
                    event.message.toLowerCase().includes('exceeded')) {
                    var warningEl = document.getElementById('storage-quota-warning');
                    if (warningEl) {
                        warningEl.style.display = 'block';
                    }
                }
            });

            // Test storage capacity
            try {
                var testKey = 'storage_test';
                var testString = new Array(512 * 1024).join('a');  // 512KB
                sessionStorage.setItem(testKey, testString);
                sessionStorage.removeItem(testKey);
            } catch (e) {
                if (e.name === 'QuotaExceededError' ||
                    (e.message &&
                    (e.message.toLowerCase().includes('quota') ||
                     e.message.toLowerCase().includes('exceeded')))) {
                    var warningEl = document.getElementById('storage-quota-warning');
                    if (warningEl) {
                        warningEl.style.display = 'block';
                    }
                }
            }
        """
        ),
        html.Div(
            [
                # Sidebar Card (retractable)
                html.Div(
                    [
                        dbc.Button(
                            id="sidebar-toggle-btn",
                            n_clicks=0,
                            color="secondary",
                            style={
                                "borderRadius": "50%",
                                "width": "36px",
                                "height": "36px",
                                "position": "absolute",
                                "top": "64px",  # moved further down from the top
                                "right": "-18px",
                                "zIndex": 10,
                                "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                                "padding": 0,
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "background": "#232323",
                                "color": "#fff",
                                "border": "2px solid #fff",
                            },
                            children=html.I(id="sidebar-toggle-icon", className="bi bi-chevron-left"),
                        ),
                        dbc.Card(
                            [
                                html.Div(
                                    [
                                        html.H4("Sidebar"),
                                        html.Hr(),
                                        search_bar,
                                    ],
                                    id="sidebar-full-content",
                                    style={"display": "block"}
                                ),
                                dbc.Nav(
                                    [
                                        dbc.NavLink(
                                            [
                                                html.I(className="fas fa-home", style={"width": "20px", "textAlign": "center", "marginRight": "12px"}),
                                                html.Span("Home", id="home-text")
                                            ],
                                            href="/",
                                            active="exact",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "8px",
                                                "color": "#ffffff",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": "400",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.I(className="fas fa-chart-bar", style={"width": "20px", "textAlign": "center", "marginRight": "12px"}),
                                                html.Span("Repo Overview", id="repo-overview-text")
                                            ],
                                            href="/repo_overview",
                                            active="exact",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "8px",
                                                "color": "#ffffff",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": "400",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.I(className="fas fa-code-branch", style={"width": "20px", "textAlign": "center", "marginRight": "12px"}),
                                                html.Span("Contributions", id="contributions-text")
                                            ],
                                            href="/contributions",
                                            active="exact",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "8px",
                                                "color": "#ffffff",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": "400",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.I(className="fas fa-users", style={"width": "20px", "textAlign": "center", "marginRight": "12px"}),
                                                html.Span("Contributors", id="contributors-text")
                                            ],
                                            href="/contributors",
                                            active="exact",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "8px",
                                                "color": "#ffffff",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": "400",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.I(className="fas fa-building", style={"width": "20px", "textAlign": "center", "marginRight": "12px"}),
                                                html.Span("Affiliation", id="affiliation-text")
                                            ],
                                            href="/affiliation",
                                            active="exact",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "8px",
                                                "color": "#ffffff",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": "400",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.I(className="fas fa-cog", style={"width": "20px", "textAlign": "center", "marginRight": "12px"}),
                                                html.Span("CHAOSS", id="chaoss-text")
                                            ],
                                            href="/chaoss",
                                            active="exact",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "8px",
                                                "color": "#ffffff",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": "400",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.I(className="fas fa-code", style={"width": "20px", "textAlign": "center", "marginRight": "12px"}),
                                                html.Span("Codebase", id="codebase-text")
                                            ],
                                            href="/codebase",
                                            active="exact",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "8px",
                                                "color": "#ffffff",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": "400",
                                            }
                                        ),
                                    ],
                                    vertical=True,
                                    className="sidebar-nav",
                                    style={"marginTop": "24px"}
                                ),
                            ],
                            id="sidebar-card",
                            style={
                                "borderRadius": "14px 0 0 14px",
                                "height": "95vh",
                                "width": "340px",
                                "background": "#232323",
                                "color": "#fff",
                                "padding": "32px 18px 32px 18px",
                                "boxShadow": "0 8px 32px rgba(0,0,0,0.12)",
                                "display": "flex",
                                "flexDirection": "column",
                                "justifyContent": "flex-start",
                                "margin": "40px 0 20px 10px",
                                "zIndex": 2,
                                "transition": "width 0.3s cubic-bezier(.4,2,.6,1)",
                                "overflow": "hidden",
                            },
                            className="sidebar-card",
                        ),
                    ],
                    id="sidebar-container",
                    style={
                        "position": "relative",
                        "transition": "width 0.3s cubic-bezier(.4,2,.6,1)",
                        "display": "flex",
                        "flexDirection": "row",
                        "alignItems": "stretch",
                    },
                ),
                # Main Card
                dbc.Card(
                    [
                        login_banner if login_banner else html.Div(),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Select GitHub repos or orgs:",
                                            html_for="projects",
                                            width="auto",
                                            size="lg",
                                        ),
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
                                                style={"marginBottom": ".5%"},
                                                text_color="dark",
                                            ),
                                            type="cube",
                                            color="#436755",
                                        ),
                                        dash.page_container,
                                    ],
                                    style={"padding": "32px"},  # Added padding to main content
                                ),
                            ],
                            justify="start",
                        ),
                    ],
                    style={
                        "borderRadius": "0 14px 14px 0",
                        "padding": "40px 40px 40px 40px",
                        "margin": "40px 10px 20px 0",
                        "width": "calc(99vw - 340px)",
                        "maxWidth": "calc(100vw - 340px)",
                        "boxShadow": "0 8px 32px rgba(0,0,0,0.12)",
                        "background": "#1D1D1D",
                        "height": "95vh",
                        "overflowY": "auto",
                        "overflowX": "hidden",
                        "display": "flex",
                        "flexDirection": "column",
                        "transition": "margin-left 0.3s cubic-bezier(.4,2,.6,1)",
                    },
                    className="big-main-card",
                    id="main-card",
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "row",
                "alignItems": "stretch",
                "width": "100vw",
            },
        ),
    ]
)

# Dash callback for sidebar toggle
@dash.callback(
    [
        Output("sidebar-card", "style"),
        Output("sidebar-full-content", "style"),
        Output("home-text", "style"),
        Output("repo-overview-text", "style"),
        Output("contributions-text", "style"),
        Output("contributors-text", "style"),
        Output("affiliation-text", "style"),
        Output("chaoss-text", "style"),
        Output("codebase-text", "style"),
        Output("main-card", "style"),
        Output("sidebar-toggle-icon", "className"),
        Output("sidebar-collapsed", "data"),
    ],
    [Input("sidebar-toggle-btn", "n_clicks")],
    [State("sidebar-collapsed", "data")],
    prevent_initial_call=True,
)
def toggle_sidebar(n, collapsed):
    if not n:
        raise dash.exceptions.PreventUpdate
    collapsed = not collapsed
    
    # Text visibility style
    text_style = {"display": "none"} if collapsed else {"display": "inline"}
    
    # Full content visibility style
    full_content_style = {"display": "none"} if collapsed else {"display": "block"}
    
    sidebar_style = {
        "borderRadius": "14px 0 0 14px",
        "height": "95vh",
        "width": "60px" if collapsed else "340px",
        "background": "#232323",
        "color": "#fff",
        "padding": "32px 6px 32px 6px" if collapsed else "32px 18px 32px 18px",
        "boxShadow": "0 8px 32px rgba(0,0,0,0.12)",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",
        "margin": "40px 0 20px 10px",
        "zIndex": 2,
        "transition": "width 0.3s cubic-bezier(.4,2,.6,1)",
        "overflow": "hidden",
    }
    main_style = {
        "borderRadius": "0 14px 14px 0",
        "padding": "40px 40px 40px 40px",
        "margin": "40px 10px 20px 0",
        "width": f"calc(99vw - {'60px' if collapsed else '340px'})",
        "maxWidth": f"calc(100vw - {'60px' if collapsed else '340px'})",
        "boxShadow": "0 8px 32px rgba(0,0,0,0.12)",
        "background": "#1D1D1D",
        "height": "95vh",
        "overflowY": "auto",
        "overflowX": "hidden",
        "display": "flex",
        "flexDirection": "column",
        "transition": "margin-left 0.3s cubic-bezier(.4,2,.6,1)",
    }
    icon = "bi bi-chevron-right" if collapsed else "bi bi-chevron-left"
    
    return (
        sidebar_style, 
        full_content_style, 
        text_style, text_style, text_style, text_style, text_style, text_style, text_style,
        main_style, 
        icon, 
        collapsed
    )
