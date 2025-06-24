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
        # Store for selected tags
        dcc.Store(id="selected-tags", storage_type="session", data=[]),
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
                        # dmc.MultiSelect(
                        #     id="projects",
                        #     searchable=True,
                        #     clearable=True,
                        #     nothingFound="No matching repos/orgs.",
                        #     variant="filled",
                        #     debounce=100,  # debounce time for the search input, since we're implementing client-side caching, we can use a faster debounce
                        #     data=[augur.initial_multiselect_option()],
                        #     value=[augur.initial_multiselect_option()["value"]],
                        #     style={"fontSize": 16},
                        #     maxDropdownHeight=300,  # limits the dropdown menu's height to 300px
                        #     zIndex=9999,  # ensures the dropdown menu is on top of other elements
                        #     dropdownPosition="bottom",  # forces the dropdown to open downwards
                        #     transitionDuration=150,  # transition duration for the dropdown menu
                        #     className="searchbar-dropdown",
                        # ),
                        html.Div(
                            [
                                # Combined search container with tags inside
                                html.Div(
                                    [
                                        # Tags display area (inside the search bar)
                                        html.Div(
                                            id="selected-tags-container",
                                            children=[],
                                            style={
                                                "display": "flex",
                                                "flexWrap": "wrap",
                                                "gap": "4px",
                                                "alignItems": "center",
                                                "paddingRight": "8px"
                                            }
                                        ),
                                        # Search input (flex-grow to fill remaining space)
                                        dcc.Input(
                                            id='my-input',
                                            type='text',
                                            placeholder='Search for repos/organizations...',
                                            style={
                                                'flex': '1',
                                                'backgroundColor': 'transparent',
                                                'color': '#fff',
                                                'border': 'none',
                                                'outline': 'none',
                                                'padding': '0',
                                                'fontSize': '16px',
                                                'minWidth': '200px'
                                            }
                                        ),
                                    ],
                                    style={
                                        'display': 'flex',
                                        'alignItems': 'center',
                                        'flexWrap': 'wrap',
                                        'backgroundColor': '#232323',
                                        'border': '1px solid #555',
                                        'borderRadius': '8px',
                                        'padding': '8px 12px',
                                        'minHeight': '44px',
                                        'gap': '4px'
                                    },
                                    id="search-input-container"
                                ),
                                # Search results popup
                                html.Div(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.Div(
                                                            id="search-results-list",
                                                            children=[
                                                                html.Div(
                                                                    "Start typing to search for repositories and organizations...",
                                                                    style={"padding": "12px", "color": "#B0B0B0", "textAlign": "center"}
                                                                )
                                                            ]
                                                        )
                                                    ],
                                                    style={"padding": "8px"}
                                                )
                                            ],
                                            style={
                                                "backgroundColor": "#2D2D2D",
                                                "border": "1px solid #555",
                                                "borderRadius": "8px",
                                                "color": "#fff"
                                            }
                                        )
                                    ],
                                    id="search-dropdown-popup",
                                    style={
                                        "position": "absolute",
                                        "top": "100%",
                                        "left": "0",
                                        "right": "0",
                                        "zIndex": "1000",
                                        "maxHeight": "300px",
                                        "overflowY": "auto",
                                        "display": "none",  # Initially hidden
                                        "marginTop": "2px"
                                    }
                                )
                            ],
                            style={
                                "position": "relative",
                                "width": "100%"
                            }
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
            // CSS for search result hover effects and inline tags
            const style = document.createElement('style');
            style.textContent = `
                .search-result-item:hover {
                    background-color: #3A3A3A !important;
                }
                .selected-tag {
                    background-color: #119DFF;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 12px;
                    font-size: 13px;
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    white-space: nowrap;
                    max-width: 200px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                .tag-remove-btn {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 14px;
                    line-height: 1;
                    padding: 0;
                    width: 14px;
                    height: 14px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    flex-shrink: 0;
                }
                .tag-remove-btn:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }
                #search-input-container:focus-within {
                    border-color: #119DFF;
                    box-shadow: 0 0 0 2px rgba(17, 157, 255, 0.2);
                }
            `;
            document.head.appendChild(style);

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


