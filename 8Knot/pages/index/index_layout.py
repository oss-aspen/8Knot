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
            html.Div(
                [
                    html.Img(
                        src=dash.get_asset_url("8KnotMainLogo.svg"),
                        height="24px",  # reduced from 32px
                        style={"margin": "8px 0 8px 32px"},  # Add left margin to shift right
                        id="main-logo-img",
                    ),
                    html.Img(
                        src=dash.get_asset_url("chaosslogo.svg"),
                        height="28px",
                        style={"margin": "8px 0 8px 16px"},  # Add left margin for spacing
                        id="chaoss-logo-img",
                    ),
                ],
                style={"display": "flex", "alignItems": "center"}
            ),
        ],
        fluid=True,
    ),
    color="dark",  # Ensures dark Bootstrap background
    style={"backgroundColor": "#131313", "border": "none", "height": "60px", "minHeight": "60px"},  # Increase navbar height
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

# Add hidden components for contributors dropdown
contributors_dropdown_state = dcc.Store(id="contributors-dropdown-open", data=False, storage_type="session")

layout = html.Div(
    [
        dcc.Store(id="repo-choices", storage_type="session", data=[]),
        dcc.Store(id="job-ids", storage_type="session", data=[]),
        dcc.Store(id="user-group-loading-signal", data="", storage_type="memory"),
        sidebar_state_store,
        contributors_dropdown_state,
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
        navbar,
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
                                "width": "32px",
                                "height": "32px",
                                "position": "absolute",
                                "top": "64px",  # moved further down from the top
                                "right": "-16px",
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
                            children=html.I(
                                id="sidebar-toggle-icon", 
                                className="fas fa-chevron-left",
                                style={
                                    "fontSize": "14px",
                                    "lineHeight": "1"
                                }
                            ),
                        ),
                        dbc.Card(
                            [
                                html.Div(
                                    [
                                        search_bar,
                                    ],
                                    id="sidebar-full-content",
                                    style={"display": "block"}
                                ),
                                dbc.Nav(
                                    [
                                        # dbc.NavLink(
                                        #     [
                                        #         html.Img(
                                        #             src=dash.get_asset_url("home.svg"),
                                        #             style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                        #         ),
                                        #         html.Span("Home", id="home-text")
                                        #     ],
                                        #     href="/",
                                        #     active="exact",
                                        #     className="sidebar-nav-link",
                                        #     style={
                                        #         "display": "flex",
                                        #         "alignItems": "center",
                                        #         "padding": "12px 16px",
                                        #         "marginBottom": "8px",
                                        #         "borderRadius": "8px",
                                        #         "color": "#ffffff",
                                        #         "textDecoration": "none",
                                        #         "fontSize": "16px",
                                        #         "fontWeight": "400",
                                        #     }
                                        # ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("repo_overview.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "Repo Overview",
                                                    id="repo-overview-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 300,   # thinner font
                                                        "fontSize": "16px",
                                                        "verticalAlign": "middle",
                                                        "letterSpacing": "0.01em",
                                                    },
                                                )
                                            ],
                                            href="/repo_overview",
                                            active="exact",
                                            id="repo-overview-navlink",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "12px",
                                                "color": "#B0B0B0",  # match icon color
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": 300,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("contributions.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "Contributions",
                                                    id="contributions-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 300,   # thinner font
                                                        "fontSize": "16px",
                                                        "verticalAlign": "middle",
                                                        "letterSpacing": "0.01em",
                                                    },
                                                )
                                            ],
                                            href="/contributions",
                                            active="exact",
                                            id="contributions-navlink",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "12px",
                                                "color": "#B0B0B0",  # match icon color
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": 300,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        # Contributors Dropdown
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Img(
                                                            src=dash.get_asset_url("contributors.svg"),
                                                            style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                        ),
                                                        html.Span(
                                                            "Contributors",
                                                            id="contributors-text",
                                                            style={
                                                                "color": "#B0B0B0",  # match icon color (light gray)
                                                                "fontWeight": 300,   # thinner font
                                                                "fontSize": "16px",
                                                                "verticalAlign": "middle",
                                                                "letterSpacing": "0.01em",
                                                            },
                                                        ),
                                                        html.I(
                                                            id="contributors-dropdown-icon",
                                                            className="bi bi-chevron-down",
                                                            style={
                                                                "marginLeft": "auto",
                                                                "fontSize": "12px",
                                                                "color": "#B0B0B0",
                                                                "transition": "transform 0.2s ease",
                                                            }
                                                        )
                                                    ],
                                                    id="contributors-dropdown-toggle",
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "padding": "12px 16px",
                                                        "borderRadius": "12px",
                                                        "color": "#B0B0B0",  # match icon color
                                                        "textDecoration": "none",
                                                        "fontSize": "16px",
                                                        "fontWeight": 300,  # thinner font
                                                        "cursor": "pointer",
                                                        "transition": "background-color 0.2s ease",
                                                    }
                                                ),
                                                html.Div(
                                                    [
                                                        dbc.NavLink(
                                                            "Behavior",
                                                            href="/contributors/behavior",
                                                            active="exact",
                                                            style={
                                                                "color": "#B0B0B0",
                                                                "fontSize": "14px",
                                                                "fontWeight": 300,
                                                                "padding": "8px 16px 8px 58px",  # indent to align with text
                                                                "marginBottom": "4px",
                                                                "borderRadius": "6px",
                                                                "textDecoration": "none",
                                                                "transition": "background-color 0.2s ease",
                                                            }
                                                        ),
                                                        dbc.NavLink(
                                                            "Contribution Types",
                                                            href="/contributors/contribution_types",
                                                            active="exact",
                                                            style={
                                                                "color": "#B0B0B0",
                                                                "fontSize": "14px",
                                                                "fontWeight": 300,
                                                                "padding": "8px 16px 8px 58px",  # indent to align with text
                                                                "marginBottom": "4px",
                                                                "borderRadius": "6px",
                                                                "textDecoration": "none",
                                                                "transition": "background-color 0.2s ease",
                                                            }
                                                        ),
                                                    ],
                                                    id="contributors-dropdown-content",
                                                    style={
                                                        "display": "none",
                                                        "paddingTop": "4px",
                                                        "borderRadius": "0 0 8px 8px",
                                                    }
                                                )
                                            ],
                                            style={
                                                "marginBottom": "8px",
                                                "borderRadius": "12px",
                                                "transition": "background-color 0.2s ease",
                                            },
                                            id="contributors-dropdown-wrapper"
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("affiliation.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "Affiliation",
                                                    id="affiliation-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 300,   # thinner font
                                                        "fontSize": "16px",
                                                        "verticalAlign": "middle",
                                                        "letterSpacing": "0.01em",
                                                    },
                                                )
                                            ],
                                            href="/affiliation",
                                            active="exact",
                                            id="affiliation-navlink",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "12px",
                                                "color": "#B0B0B0",  # match icon color
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": 300,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("chaoss.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "CHAOSS",
                                                    id="chaoss-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 300,   # thinner font
                                                        "fontSize": "16px",
                                                        "verticalAlign": "middle",
                                                        "letterSpacing": "0.01em",
                                                    },
                                                )
                                            ],
                                            href="/chaoss",
                                            active="exact",
                                            id="chaoss-navlink",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "12px",
                                                "color": "#B0B0B0",  # match icon color
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": 300,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("codebase.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "Codebase",
                                                    id="codebase-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 300,   # thinner font
                                                        "fontSize": "16px",
                                                        "verticalAlign": "middle",
                                                        "letterSpacing": "0.01em",
                                                    },
                                                )
                                            ],
                                            href="/codebase",
                                            active="exact",
                                            id="codebase-navlink",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "padding": "12px 16px",
                                                "marginBottom": "8px",
                                                "borderRadius": "12px",
                                                "color": "#B0B0B0",  # match icon color
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": 300,  # thinner font
                                                "transition": "background-color 0.2s ease",
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
                                "background": "#1D1D1D",
                                "color": "#fff",
                                "padding": "32px 18px 32px 18px",
                                "boxShadow": "none",  # Remove shadow from sidebar card
                                "borderRight": "1px solid #404040",
                                "display": "flex",
                                "flexDirection": "column",
                                "justifyContent": "flex-start",
                                "margin": "0px 0 20px 10px",  # set top margin to 0 to remove space below navbar
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
                        "background": "#242424",  # set background for sidebar container back to #242424
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
                                        # dbc.Label(
                                        #     "Select GitHub repos or orgs:",
                                        #     html_for="projects",
                                        #     width="auto",
                                        #     size="lg",
                                        # ),
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
                        "padding": "0px 40px 40px 40px",  # set top padding to 0 to remove space below navbar
                        "margin": "0px 10px 20px 0",      # set top margin to 0 to remove space below navbar
                        "width": "calc(99vw - 340px)",
                        "maxWidth": "calc(100vw - 340px)",
                        "boxShadow": "none",  # Remove shadow from main card
                        "background": "#1D1D1D",
                        "height": "95vh",
                        "overflowY": "auto",
                        "overflowX": "hidden",
                        "display": "flex",
                        "flexDirection": "column",
                        "transition": "margin-left 0.3s cubic-bezier(.4,2,.6,1)",
                        "marginLeft": "0",
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
                "background": "#242424",  # set background for the flex row
            },
        ),
    ]
)

# Dash callback for sidebar toggle
@dash.callback(
    [
        Output("sidebar-card", "style"),
        Output("sidebar-full-content", "style"),
        # Output("home-text", "style"),
        Output("repo-overview-text", "style"),
        Output("contributions-text", "style"),
        Output("contributors-text", "style"),
        Output("affiliation-text", "style"),
        Output("chaoss-text", "style"),
        Output("codebase-text", "style"),
        Output("main-card", "style"),
        Output("sidebar-toggle-icon", "className"),
        Output("sidebar-collapsed", "data"),
        # Contributors dropdown outputs to close dropdown when sidebar collapses
        Output("contributors-dropdown-content", "style", allow_duplicate=True),
        Output("contributors-dropdown-icon", "className", allow_duplicate=True),
        Output("contributors-dropdown-open", "data", allow_duplicate=True),
        Output("contributors-dropdown-wrapper", "className", allow_duplicate=True),
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
        "width": "80px" if collapsed else "340px",
        "background": "#1D1D1D",  # FIXED: match static style
        "color": "#fff",
        "padding": "32px 12px 32px 12px" if collapsed else "32px 18px 32px 18px",
        "boxShadow": "none",  # Remove shadow from sidebar card
        "borderRight": "1px solid #404040",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",
        "margin": "0px 0 20px 10px",  # always 0 top margin to keep content flush with navbar
        "zIndex": 2,
        "transition": "width 0.3s cubic-bezier(.4,2,.6,1)",
        "overflow": "hidden",
    }
    main_style = {
        "borderRadius": "0 14px 14px 0",
        "padding": "0px 40px 40px 40px",  # always 0 top padding
        "margin": "0px 10px 20px 0",      # always 0 top margin
        "width": f"calc(99vw - {'80px' if collapsed else '340px'})",
        "maxWidth": f"calc(100vw - {'80px' if collapsed else '340px'})",
        "boxShadow": "none",  # Remove shadow from main card
        "background": "#1D1D1D",  # FIXED: match static style
        "height": "95vh",
        "overflowY": "auto",
        "overflowX": "hidden",
        "display": "flex",
        "flexDirection": "column",
        "transition": "margin-left 0.3s cubic-bezier(.4,2,.6,1)",
        "marginLeft": "0",
    }
    icon = "fas fa-chevron-right" if collapsed else "fas fa-chevron-left"
    
    # When sidebar is collapsed, always close the contributors dropdown
    if collapsed:
        dropdown_content_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
        dropdown_icon_class = "bi bi-chevron-down"
        dropdown_open = False
        dropdown_wrapper_class = ""
    else:
        # When sidebar is expanded, don't change dropdown state - use dash.no_update
        dropdown_content_style = dash.no_update
        dropdown_icon_class = dash.no_update
        dropdown_open = dash.no_update
        dropdown_wrapper_class = dash.no_update
    
    return (
        sidebar_style, 
        full_content_style, 
        text_style, text_style, text_style, text_style, text_style, text_style,
        main_style, 
        icon, 
        collapsed,
        dropdown_content_style,
        dropdown_icon_class,
        dropdown_open,
        dropdown_wrapper_class
    )

# Callback for contributors dropdown
@dash.callback(
    [
        Output("contributors-dropdown-content", "style"),
        Output("contributors-dropdown-icon", "className"),
        Output("contributors-dropdown-open", "data"),
        Output("sidebar-collapsed", "data", allow_duplicate=True),
        Output("contributors-dropdown-wrapper", "className"),
        Output("sidebar-card", "style", allow_duplicate=True),
        Output("sidebar-full-content", "style", allow_duplicate=True),
        Output("repo-overview-text", "style", allow_duplicate=True),
        Output("contributions-text", "style", allow_duplicate=True),
        Output("contributors-text", "style", allow_duplicate=True),
        Output("affiliation-text", "style", allow_duplicate=True),
        Output("chaoss-text", "style", allow_duplicate=True),
        Output("codebase-text", "style", allow_duplicate=True),
        Output("main-card", "style", allow_duplicate=True),
        Output("sidebar-toggle-icon", "className", allow_duplicate=True),
    ],
    [
        Input("contributors-dropdown-toggle", "n_clicks"),
        Input("repo-overview-navlink", "n_clicks"),
        Input("contributions-navlink", "n_clicks"), 
        Input("affiliation-navlink", "n_clicks"),
        Input("chaoss-navlink", "n_clicks"),
        Input("codebase-navlink", "n_clicks"),
    ],
    [
        State("contributors-dropdown-open", "data"),
        State("sidebar-collapsed", "data"),
    ],
    prevent_initial_call=True,
)
def toggle_contributors_dropdown(dropdown_clicks, repo_clicks, contrib_clicks, aff_clicks, chaoss_clicks, code_clicks, dropdown_open, sidebar_collapsed):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # If any other navlink was clicked, close dropdown but don't change sidebar
    if trigger_id in ["repo-overview-navlink", "contributions-navlink", "affiliation-navlink", "chaoss-navlink", "codebase-navlink"]:
        dropdown_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
        icon_class = "bi bi-chevron-down"
        wrapper_class = ""
        # Return current sidebar state unchanged - use dash.no_update for all sidebar-related outputs
        return dropdown_style, icon_class, False, sidebar_collapsed, wrapper_class, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # If contributors dropdown toggle was clicked
    if trigger_id == "contributors-dropdown-toggle":
        # ALWAYS expand the sidebar when contributors dropdown is clicked
        dropdown_open = not dropdown_open
        
        if dropdown_open:
            dropdown_style = {"display": "block", "paddingTop": "4px", "borderRadius": "0 0 8px 8px"}
            wrapper_class = "dropdown-open"
        else:
            dropdown_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
            wrapper_class = ""
        
        icon_class = "bi bi-chevron-up" if dropdown_open else "bi bi-chevron-down"
        
        # Force sidebar to expanded state (like circular button click)
        collapsed = False  # Always expanded
        
        # Text visibility style (expanded)
        text_style = {"display": "inline"}
        
        # Contributors dropdown icon style (expanded)
        dropdown_icon_style = {
            "marginLeft": "auto",
            "fontSize": "12px",
            "color": "#B0B0B0",
            "display": "inline"
        }
        
        # Full content visibility style (expanded)
        full_content_style = {"display": "block"}
        
        # Sidebar style (expanded)
        sidebar_style = {
            "borderRadius": "14px 0 0 14px",
            "height": "95vh",
            "width": "340px",
            "background": "#1D1D1D",
            "color": "#fff",
            "padding": "32px 18px 32px 18px",
            "boxShadow": "none",
            "borderRight": "1px solid #404040",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flex-start",
            "margin": "0px 0 20px 10px",
            "zIndex": 2,
            "transition": "width 0.3s cubic-bezier(.4,2,.6,1)",
            "overflow": "hidden",
        }
        
        # Main card style (expanded)
        main_style = {
            "borderRadius": "0 14px 14px 0",
            "padding": "0px 40px 40px 40px",
            "margin": "0px 10px 20px 0",
            "width": "calc(99vw - 340px)",
            "maxWidth": "calc(100vw - 340px)",
            "boxShadow": "none",
            "background": "#1D1D1D",
            "height": "95vh",
            "overflowY": "auto",
            "overflowX": "hidden",
            "display": "flex",
            "flexDirection": "column",
            "transition": "margin-left 0.3s cubic-bezier(.4,2,.6,1)",
            "marginLeft": "0",
        }
        
        # Toggle icon (expanded)
        toggle_icon = "fas fa-chevron-left"
        
        return dropdown_style, icon_class, dropdown_open, collapsed, wrapper_class, sidebar_style, full_content_style, text_style, text_style, text_style, text_style, text_style, text_style, main_style, toggle_icon
    
    raise dash.exceptions.PreventUpdate
