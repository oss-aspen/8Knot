from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from app import augur
import os
import logging

# Import layout components
from .index_components import (
    sidebar_section,
    sidebar_dropdown,
    create_main_content_area,
    create_sidebar_navigation,
    create_sidebar,
    create_main_layout,
    create_app_stores,
    create_storage_quota_script,
    initialize_components,
)

# Note: Welcome sections are now imported in pages/landing/landing.py

# Top bar with logos and navigation links
topbar = html.Div(
    [
        # Left section with hamburger menu and logos
        html.Div(
            [
                # Hamburger menu toggle button
                dbc.Button(
                    html.I(className="fas fa-bars sidebar-toggle-icon"),
                    id="sidebar-toggle",
                    color="link",
                    size="sm",
                    className="sidebar-toggle",
                ),
                html.Img(
                    src="/assets/8Knot.svg",
                    alt="8Knot Logo",
                    className="logo",
                ),
                html.Img(
                    src="/assets/CHAOSS.svg",
                    alt="CHAOSS Logo",
                    className="logo logo--chaoss",
                ),
            ],
            className="topbar-left",
        ),
        # Middle section with navigation links
        html.Div(
            [
                dbc.NavLink(
                    "Welcome",
                    href="/",
                    active="exact",
                    className="nav-link",
                ),
                dbc.NavLink(
                    "Visualizations",
                    href="/repo_overview",
                    active="exact",
                    className="nav-link nav-link--visualization",
                ),
            ],
            className="topbar-center",
        ),
        # Right section (empty for now, can be used for future additions)
        html.Div(className="topbar-right"),
    ],
    id="rectangular-bar",
    className="topbar",
)


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
            duration=60000,
            id="login-disabled-banner",
            className="mb-0",
            style={
                "backgroundColor": "#DFF0FB",  # Light blue background
                "borderColor": "#0F5880",  # Darker blue border from palette
                "border": "1px solid #0F5880",
                "borderLeft": "5px solid #0F5880",
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
        # Search input section
        html.Div(
            [
                html.Div(
                    [
                        dmc.MultiSelect(
                            id="projects",
                            searchable=True,
                            clearable=True,
                            nothingFoundMessage="No matching repos/orgs.",
                            placeholder="Search",
                            variant="filled",
                            debounce=100,  # debounce time for the search input, since we're implementing client-side caching, we can use a faster debounce
                            data=[augur.initial_multiselect_option()],
                            value=[augur.initial_multiselect_option()["value"]],
                            className="searchbar-dropdown",
                            styles={
                                "input": {
                                    "fontSize": "16px",
                                    "minHeight": "48px",
                                    "height": "auto",
                                    "padding": "12px 16px 12px 44px",
                                    "borderRadius": "20px",
                                    "display": "flex",
                                    "flexWrap": "wrap",
                                    "alignItems": "flex-start",
                                    "backgroundColor": "#1D1D1D",
                                    "borderColor": "#404040",
                                    "position": "relative",
                                    "zIndex": 1,
                                },
                                "dropdown": {
                                    "borderRadius": "12px",
                                    "backgroundColor": "#1D1D1D",
                                    "border": "1px solid #444",
                                },
                                "item": {
                                    "borderRadius": "8px",
                                    "margin": "2px 4px",
                                    "color": "white",
                                },
                            },
                        ),
                        dbc.Button(
                            html.I(className="fas fa-search"),
                            id="search",
                            n_clicks=0,
                            size="sm",
                            color="outline-secondary",
                            title="Search",
                            style={
                                "backgroundColor": "transparent",
                                "border": "none",
                                "fontSize": "16px",
                                "width": "16px",
                                "height": "16px",
                                "position": "absolute",
                                "left": "10px",
                                "top": "50%",
                                "transform": "translateY(-50%)",
                                "fontWeight": "bold",
                                "zIndex": 1,
                            },
                        ),
                    ],
                    style={"position": "relative"},
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
                "marginBottom": "1rem",
                "padding": "0 6px",
            },
        ),
        dbc.Stack(
            [
                dbc.Button(
                    html.I(className="fas fa-question-circle"),
                    id="search-help",
                    n_clicks=0,
                    size="sm",
                    color="outline-secondary",
                    title="Help",
                    style={
                        "backgroundColor": "transparent",
                        "border": "none",
                        "padding": "4px 8px",
                        "fontSize": "14px",
                    },
                ),
                dbc.Button(
                    html.I(className="fas fa-list"),
                    id="repo-list-button",
                    n_clicks=0,
                    size="sm",
                    color="outline-secondary",
                    title="Repo List",
                    style={
                        "backgroundColor": "transparent",
                        "border": "none",
                        "padding": "4px 8px",
                        "fontSize": "14px",
                    },
                ),
                dbc.Switch(
                    id="bot-switch",
                    label="GitHub Bot Filter",
                    value=True,
                    input_class_name="botlist-filter-switch",
                    style={"fontSize": 12, "marginTop": "8px", "marginLeft": "10px"},
                ),
            ],
            direction="horizontal",
            style={
                "width": "100%",
                "justifyContent": "center",
                "marginTop": "16px",
            },
        ),
    ],
    style={"paddingTop": "16px"},  # Top padding adjusted slightly
)

navbar_bottom = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            dbc.NavLink(
                "Visualization request",
                href="https://github.com/oss-aspen/8Knot/issues/new?assignees=&labels=enhancement%2Cvisualization&template=visualizations.md",
                external_link="True",
                target="_blank",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Bug",
                href="https://github.com/oss-aspen/8Knot/issues/new?assignees=&labels=bug&template=bug_report.md",
                external_link="True",
                target="_blank",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Repo/Org Request",
                href="https://github.com/oss-aspen/8Knot/issues/new?assignees=&labels=augur&template=augur_load.md",
                external_link="True",
                target="_blank",
            )
        ),
    ],
    brand="",
    brand_href="#",
    fluid=True,
    fixed="bottom",
    color="#1D1D1D",
    dark=True,
)

# Initialize components with required references
initialize_components(search_bar)

# Note: Index layout provides the main application structure
# The landing page is now registered separately in pages/landing/landing.py

# Main application layout
layout = html.Div(
    dbc.Container(
        [
            # Application stores and scripts
            *create_app_stores(),
            create_storage_quota_script(),
            # Login banner overlay
            login_banner if login_banner else html.Div(),
            # Main application structure
            dbc.Row(
                [
                    dbc.Col(
                        [
                            topbar,
                            create_main_layout(),
                        ],
                    ),
                ],
                justify="start",
            ),
            navbar_bottom,
        ],
        fluid=True,
        className="dbc app-main-container",
    ),
    className="app-container",
)
