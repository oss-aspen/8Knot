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
                                        'borderRadius': '16px',
                                        'padding': '8px 12px',
                                        'minHeight': '44px',
                                        'gap': '4px'
                                    },
                                    id="search-input-container"
                                ),
                                # Search results popup
                                html.Div(
                                    [
                                        # First card: Searchable content (scrollable) - moved to top
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
                                                "backgroundColor": "#292929",
                                                "border": "1px solid #555",
                                                "borderRadius": "16px 16px 0 0",  # Rounded top corners only
                                                "borderBottom": "none",  # No bottom border to connect with second card
                                                "color": "#fff",
                                                "maxHeight": "240px",  # Limit height for scrolling
                                                "overflowY": "auto",  # Make this card scrollable
                                                "marginBottom": "0"  # No margin between cards
                                            }
                                        ),
                                        # Second card: Options and controls - moved to bottom
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        # Action buttons at the top of dropdown
                                                        html.Div(
                                                            [
                                                                dbc.Button(
                                                                    "Search",
                                                                    id="search",
                                                                    n_clicks=0,
                                                                    size="sm",
                                                                    color="primary",
                                                                    style={
                                                                        "fontSize": "12px",
                                                                        "padding": "4px 12px",
                                                                        "backgroundColor": "#119DFF",
                                                                        "borderColor": "#119DFF",
                                                                        "color": "#fff"
                                                                    }
                                                                ),
                                                                dbc.Button(
                                                                    "Help",
                                                                    id="search-help",
                                                                    n_clicks=0,
                                                                    size="sm",
                                                                    color="secondary",
                                                                    outline=True,
                                                                    style={
                                                                        "fontSize": "12px",
                                                                        "padding": "4px 8px",
                                                                        "borderColor": "#555",
                                                                        "color": "#B0B0B0"
                                                                    }
                                                                ),
                                                                dbc.Button(
                                                                    "Repo List",
                                                                    id="repo-list-button",
                                                                    n_clicks=0,
                                                                    size="sm",
                                                                    color="secondary",
                                                                    outline=True,
                                                                    style={
                                                                        "fontSize": "12px",
                                                                        "padding": "4px 8px",
                                                                        "borderColor": "#555",
                                                                        "color": "#B0B0B0"
                                                                    }
                                                                ),
                                                            ],
                                                            style={
                                                                "borderBottom": "1px solid #555", 
                                                                "paddingBottom": "8px", 
                                                                "marginBottom": "8px",
                                                                "display": "flex",
                                                                "justifyContent": "center",
                                                                "gap": "8px"
                                                            }
                                                        ),
                                                        # Bot filter switch below the buttons
                                                        html.Div(
                                                            [
                                                                dbc.Switch(
                                                                    id="bot-switch",
                                                                    label="GitHub Bot Filter",
                                                                    value=True,
                                                                    input_class_name="botlist-filter-switch",
                                                                    style={"fontSize": 14},
                                                                ),
                                                            ],
                                                            style={
                                                                "display": "flex",
                                                                "justifyContent": "center"
                                                            }
                                                        )
                                                    ],
                                                    style={"padding": "8px"}
                                                )
                                            ],
                                            style={
                                                "backgroundColor": "#292929",
                                                "border": "1px solid #555",
                                                "borderRadius": "0 0 16px 16px",  # Rounded bottom corners only
                                                "borderTop": "none",  # No top border to connect with first card
                                                "color": "#fff",
                                                "marginTop": "0"  # No margin between cards
                                            }
                                        )
                                    ],
                                    id="search-dropdown-popup",
                                    **{"data-click-outside-initialized": "false"},
                                    style={
                                        "position": "absolute",
                                        "top": "100%",
                                        "left": "0",
                                        "right": "0",
                                        "zIndex": "1000",
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
                            style={"zIndex": "1100"},  # Higher than search dropdown (1000)
                        ),
                        dbc.Alert(
                            children="List of repos",
                            id="repo-list-alert",
                            dismissable=True,
                            fade=True,
                            is_open=False,
                            color="light",
                            # if number of repos is large, render as a scrolling window
                            style={"overflow-y": "scroll", "max-height": "440px", "zIndex": "1100"},  # Higher than search dropdown (1000)
                        ),
                    ],
                    style={
                        "width": "100%",
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
                                "width": "24px",
                                "height": "24px",
                                "position": "absolute",
                                "top": "64px",  # moved further down from the top
                                "right": "-12px",
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
                                    "fontSize": "10px",
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
                                        # Dummy Search NavLink - only visible when sidebar is collapsed
                                        dbc.NavLink(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-search",
                                                            style={
                                                                "fontSize": "16px",
                                                                "color": "#B0B0B0",
                                                                "lineHeight": "1",
                                                            }
                                                        )
                                                    ],
                                                    style={
                                                        "width": "60px",
                                                        "height": "60px",
                                                        "borderRadius": "50%",
                                                        "border": "2px solid #404040",
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "marginRight": "12px",
                                                        "flexShrink": "0",
                                                    }
                                                ),
                                                html.Span(
                                                    "Search",
                                                    id="dummy-search-text",
                                                    style={
                                                        "color": "#B0B0B0",
                                                        "fontWeight": 400,
                                                        "fontSize": "16px",
                                                        "verticalAlign": "middle",
                                                        "letterSpacing": "0.01em",
                                                        "display": "none",  # Hidden by default
                                                    },
                                                )
                                            ],
                                            href="#",  # dummy link
                                            id="dummy-search-navlink",
                                            className="sidebar-nav-link",
                                            style={
                                                "display": "none",  # Hidden by default, shown only when collapsed
                                                "alignItems": "center",
                                                "padding": "12px 8px",  # Reduced left/right padding from 16px to 8px
                                                "marginBottom": "24px",  # More spacing before next navlink
                                                "marginTop": "-40px",  # Move up relative to sidebar
                                                "marginLeft": "0",  # Centering handled by calculated padding
                                                "borderRadius": "12px",
                                                "color": "#B0B0B0",
                                                "textDecoration": "none",
                                                "fontSize": "16px",
                                                "fontWeight": 400,
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("sidebar/repo_overview.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "Repo Overview",
                                                    id="repo-overview-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 400,   # thinner font
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
                                                "fontWeight": 400,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("sidebar/contributions.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "Contributions",
                                                    id="contributions-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 400,   # thinner font
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
                                                "fontWeight": 400,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        # Contributors Dropdown
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Img(
                                                            src=dash.get_asset_url("sidebar/contributors.svg"),
                                                            style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                        ),
                                                        html.Span(
                                                            "Contributors",
                                                            id="contributors-text",
                                                            style={
                                                                "color": "#B0B0B0",  # match icon color (light gray)
                                                                "fontWeight": 400,   # thinner font
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
                                                        "fontWeight": 400,  # thinner font
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
                                                                "fontWeight": 400,
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
                                                                "fontWeight": 400,
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
                                                    src=dash.get_asset_url("sidebar/affiliation.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "Affiliation",
                                                    id="affiliation-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 400,   # thinner font
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
                                                "fontWeight": 400,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        dbc.NavLink(
                                            [
                                                html.Img(
                                                    src=dash.get_asset_url("sidebar/chaoss.svg"),
                                                    style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                                ),
                                                html.Span(
                                                    "CHAOSS",
                                                    id="chaoss-text",
                                                    style={
                                                        "color": "#B0B0B0",  # match icon color (light gray)
                                                        "fontWeight": 400,   # thinner font
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
                                                "fontWeight": 400,  # thinner font
                                                "transition": "background-color 0.2s ease",
                                            }
                                        ),
                                        # dbc.NavLink(
                                        #     [
                                        #         html.Img(
                                        #             src=dash.get_asset_url("sidebar/codebase.svg"),
                                        #             style={"width": "30px", "height": "30px", "marginRight": "12px", "verticalAlign": "middle"},
                                        #         ),
                                        #         html.Span(
                                        #             "Codebase",
                                        #             id="codebase-text",
                                        #             style={
                                        #                 "color": "#B0B0B0",  # match icon color (light gray)
                                        #                 "fontWeight": 300,   # thinner font
                                        #                 "fontSize": "16px",
                                        #                 "verticalAlign": "middle",
                                        #                 "letterSpacing": "0.01em",
                                        #             },
                                        #         )
                                        #     ],
                                        #     href="/codebase",
                                        #     active="exact",
                                        #     id="codebase-navlink",
                                        #     className="sidebar-nav-link",
                                        #     style={
                                        #         "display": "flex",
                                        #         "alignItems": "center",
                                        #         "padding": "12px 16px",
                                        #         "marginBottom": "8px",
                                        #         "borderRadius": "12px",
                                        #         "color": "#B0B0B0",  # match icon color
                                        #         "textDecoration": "none",
                                        #         "fontSize": "16px",
                                        #         "fontWeight": 300,  # thinner font
                                        #         "transition": "background-color 0.2s ease",
                                        #     }
                                        # ),
                                    ],
                                    vertical=True,
                                    className="sidebar-nav",
                                    style={"marginTop": "24px"}
                                ),
                            ],
                            id="sidebar-card",
                            style={
                                "borderRadius": "14px 0 0 14px",
                                "width": "340px",
                                "background": "#1D1D1D",
                                "color": "#fff",
                                "padding": "32px 18px 32px 18px",
                                "boxShadow": "none",  # Remove shadow from sidebar card
                                "border": "none",  # Remove all default borders
                                "borderRight": "1px solid #404040",  # Keep only right border
                                "display": "flex",
                                "flexDirection": "column",
                                "justifyContent": "flex-start",
                                "margin": "0px",  # Remove all margins, spacing handled by container padding
                                "zIndex": 2,
                                "overflow": "hidden",
                                "flex": "0 0 auto",  # Don't grow or shrink
                            },
                            className="sidebar-card",
                        ),
                    ],
                    id="sidebar-container",
                    style={
                        "position": "relative",
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
                                        html.Div(dash.page_container, id="page-container-wrapper"),
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
                        "margin": "0px",  # Remove all margins, spacing handled by container padding
                        "boxShadow": "none",  # Remove shadow from main card
                        "border": "none",  # Remove all default borders
                        "background": "#1D1D1D",
                        "overflowY": "auto",
                        "overflowX": "hidden",
                        "display": "flex",
                        "flexDirection": "column",
                        "marginLeft": "0",
                        "flex": "1",  # Grow to fill remaining space
                    },
                    className="big-main-card",
                    id="main-card",
                ),
            ],
            style={
                "display": "flex",
                "flexDirection": "row",
                "alignItems": "stretch",
                "height": "calc(100vh - 90px)",  # Full viewport minus navbar and dev tools bar
                "padding": "0px 10px 0px 10px",  # top right bottom left - normal bottom padding
                "background": "#242424",  # set background for the flex row
                "boxSizing": "border-box",
            },
        ),
    ],
    style={
        "background": "#242424 !important",  # Match the main container background
    }
)


