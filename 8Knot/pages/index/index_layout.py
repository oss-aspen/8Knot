from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from app import augur
import os
import logging

#
def sidebar_section(icon_src=None, text="Hello", page_link="/", horizontal_padding=12, vertical_padding=16):
    """
    Creates a clickable section in the sidebar, which allows navigation to different pages

    Args:
        icon_src: Optionally label the section with an icon
        text: The text that will be displayed in the sidebar section
        page_link: The page to navigate to
        horizontal_padding and vertical_padding: Fine-tune the spacing
    """
    if icon_src:
        return dbc.NavLink(
            [
                html.Img(src=icon_src, alt=text, style={"width": "24px", "height": "24px", "marginRight": "12px"}),
                html.Span(text, style={"color": "#9c9c9c", "fontSize": "16px", "fontWeight": "400"}),
            ],
            href=page_link,
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": f"{horizontal_padding}px {vertical_padding}px",
                "borderRadius": "8px",
                "marginBottom": "8px",
                "textDecoration": "none",
            },
        )
    else:
        return dbc.NavLink(
            text,
            href=page_link,
            style={
                "color": "#9c9c9c",
                "fontSize": "14px",
                "padding": f"{horizontal_padding}px {vertical_padding}px",
                "marginBottom": "4px",
                "textDecoration": "none",
                "display": "block",
            },
        )


def sidebar_dropdown(
    icon_src, text, dropdown_links, dropdown_id="dropdown", horizontal_padding=12, vertical_padding=16
):
    """Create a dropdown navigation with main item and dropdown content

    Args:
        icon_src (str): Source path for the icon image
        text (str): Text to display next to the icon
        dropdown_links (list): List of dropdown link components
        dropdown_id (str): Unique identifier for this dropdown (default: "dropdown")
        horizontal_padding (int): Horizontal padding for the toggle button
        vertical_padding (int): Vertical padding for the toggle button
    """
    return html.Div(
        [
            html.Div(
                [
                    html.Img(
                        src=icon_src,
                        alt=text,
                        style={"width": "24px", "height": "24px", "marginRight": "12px"},
                    ),
                    html.Span(text, style={"color": "#9c9c9c", "fontSize": "16px", "fontWeight": "400"}),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "padding": f"{horizontal_padding}px {vertical_padding}px",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                },
                id={"type": "sidebar-dropdown-toggle", "index": dropdown_id},
            ),
            html.Div(
                dropdown_links,
                id={"type": "sidebar-dropdown-content", "index": dropdown_id},
                style={"display": "none", "padding": "8px 0", "borderRadius": "0 0 8px 8px"},
            ),
        ],
        id={"type": "sidebar-dropdown-container", "index": dropdown_id},
        style={"borderRadius": "8px", "marginBottom": "8px"},
    )


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
                    style={
                        "color": "#9c9c9c",
                        "fontSize": "18px",
                        "padding": "8px 12px",
                        "marginRight": "10px",
                        "border": "none",
                        "backgroundColor": "transparent",
                    },
                ),
                html.Img(
                    src="/assets/8Knot.svg",
                    alt="8Knot Logo",
                    style={
                        "width": "70px",
                        "height": "22px",
                        "margin": "20px 20px",
                        "display": "inline-block",
                        "verticalAlign": "middle",
                    },
                ),
                html.Img(
                    src="/assets/CHAOSS.svg",
                    alt="CHAOSS Logo",
                    style={
                        "width": "70px",
                        "height": "22px",
                        "margin": "10px -20px",
                        "display": "inline-block",
                        "verticalAlign": "middle",
                    },
                ),
            ],
            style={"display": "flex", "alignItems": "center"},
        ),
        # Middle section with navigation links (moved from sidebar footer)
        html.Div(
            [
                dbc.NavLink(
                    "Welcome",
                    href="/",
                    external_link=True,
                    target="_self",
                    style={
                        "color": "#9c9c9c",
                        "fontSize": "16px",
                        "padding": "6px 16px",
                        "marginRight": "16px",
                        "textDecoration": "none",
                        "borderRadius": "8px",
                        "lineHeight": "1.2",
                    },
                ),
                dbc.NavLink(
                    "Visualizations",
                    href="/repo_overview",
                    active="exact",
                    style={
                        "backgroundColor": "transparent",
                        "border": "none",
                        "color": "#9c9c9c",
                        "fontSize": "16px",
                        "textAlign": "left",
                        "padding": "4px 16px",
                        "borderRadius": "8px",
                        "textDecoration": "none",
                        "lineHeight": "1.2",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "flex": "1",
            },
        ),
        # Right section (empty for now, can be used for future additions)
        html.Div(
            style={"minWidth": "150px"},  # Balances the left section
        ),
    ],
    id="rectangular-bar",
    style={
        "height": "60px",
        "width": "100%",
        "background-color": "#1D1D1D",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "paddingLeft": "10px",
        "paddingRight": "10px",
        "border-bottom": "1.5px solid #292929",
    },
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
                            nothingFound="No matching repos/orgs.",
                            placeholder="Search",
                            variant="filled",
                            debounce=100,  # debounce time for the search input, since we're implementing client-side caching, we can use a faster debounce
                            data=[augur.initial_multiselect_option()],
                            value=[augur.initial_multiselect_option()["value"]],
                            className="searchbar-dropdown",
                            styles={
                                "input": {
                                    "fontSize": "16px",
                                    "height": "48px",
                                    "padding": "0 16px 0 44px",
                                    "borderRadius": "20px",
                                    "display": "flex",
                                    "alignItems": "center",
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
                                "transform": "translateY(-100%)",
                                "fontWeight": "bold",
                                "zIndex": 2,
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

# We need to wrap the container in a div to allow for custom styling
layout = html.Div(
    dbc.Container(
        [
            # componets to store data from queries
            dcc.Store(id="repo-choices", storage_type="session", data=[]),
            # components to store job-ids for the worker queue
            dcc.Store(id="job-ids", storage_type="session", data=[]),
            dcc.Store(id="user-group-loading-signal", data="", storage_type="memory"),
            dcc.Location(id="url"),
            # Add client-side script to handle storage quota issues
            # This script does two things:
            # 1. Listens for global JavaScript errors related to storage quota being exceeded.
            #    If such an error occurs, finds the element with id 'storage-quota-warning'
            #    and makes it visible to alert the user.
            # 2. Tests if sessionStorage can store a 512KB string.
            #    If the test fails (due to quota limits), it displays the warning.
            # The user will see the warning if the browser's session storage is full
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
            # navbar,
            # Add login banner overlay (will be positioned via CSS)
            login_banner if login_banner else html.Div(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            topbar,
                            # where our page will be rendered
                            # We are wrapping this in a div to allow for custom styling
                            html.Div(
                                [
                                    # Left sidebar with dbc.Collapse
                                    dbc.Collapse(
                                        html.Div(
                                            [
                                                # Sidebar body (grows), contains search and nav
                                                html.Div(
                                                    [
                                                        search_bar,
                                                        # Navigation menu
                                                        html.Div(
                                                            [
                                                                sidebar_section(
                                                                    "/assets/repo_overview.svg",
                                                                    "Repo Overview",
                                                                    "/repo_overview",
                                                                ),
                                                                sidebar_section(
                                                                    "/assets/contributions.svg",
                                                                    "Contributions",
                                                                    "/contributions",
                                                                ),
                                                                sidebar_dropdown(
                                                                    "/assets/contributors.svg",
                                                                    "Contributors",
                                                                    [
                                                                        sidebar_section(
                                                                            icon_src=None,
                                                                            text="Behavior",
                                                                            page_link="/contributors/behavior",
                                                                        ),
                                                                        sidebar_section(
                                                                            text="Contribution Types",
                                                                            page_link="/contributors/contribution_types",
                                                                        ),
                                                                    ],
                                                                    dropdown_id="contributors-dropdown",
                                                                ),
                                                                sidebar_section(
                                                                    "/assets/affiliation.svg",
                                                                    "Affiliation",
                                                                    "/affiliation",
                                                                ),
                                                                sidebar_section(
                                                                    "/assets/chaoss_small.svg", "CHAOSS", "/chaoss"
                                                                ),
                                                            ],
                                                            style={"marginTop": "2rem", "paddingLeft": "6px"},
                                                        ),
                                                    ],
                                                    style={"flex": "1 1 auto", "overflowY": "auto"},
                                                ),
                                            ],
                                            style={
                                                "width": "340px",
                                                "background-color": "#1D1D1D",
                                                "border-radius": "12px 0 0 12px",
                                                "border-right": "1.5px solid #292929",
                                                "padding": "1rem",
                                                "flex-shrink": 0,
                                                "display": "flex",
                                                "flexDirection": "column",
                                                "height": "calc(100vh - 60px - 56px - 4px)",
                                                "overflow": "hidden",
                                            },
                                        ),
                                        id="sidebar-collapse",
                                        is_open=False,  # Start with sidebar collapsed
                                        dimension="width",  # Collapse horizontally
                                    ),
                                    # Main content area (your existing page-container)
                                    html.Div(
                                        [
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
                                                    color="#0F5880",
                                                    className="me-1",
                                                    style={"marginBottom": ".5%"},
                                                    # text_color="dark",
                                                ),
                                                type="cube",
                                                color="#0F5880",
                                            ),
                                            dash.page_container,
                                        ],
                                        id="page-container",
                                        style={
                                            "border-radius": "0 12px 12px 0",
                                            "background-color": "#1D1D1D",
                                            "padding": "1rem",
                                            "overflow-y": "auto",
                                            "height": "100%",
                                            "flex": "1",
                                        },
                                    ),
                                ],
                                id="main-layout-container",
                                style={
                                    "display": "flex",
                                    "height": "calc(100vh - 60px - 56px - 4px)",
                                },
                            ),
                        ],
                    ),
                ],
                justify="start",
            ),
            # Bottom navbar fixed to viewport bottom (render last)
            navbar_bottom,
        ],
        fluid=True,
        className="dbc",
        style={
            "background-color": "#242424",
        },
    ),
    style={"background-color": "#242424", "min-height": "100vh", "margin": "0", "padding": "0"},
)
