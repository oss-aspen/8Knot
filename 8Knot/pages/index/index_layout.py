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
    return dbc.Card(
        [
            dbc.CardBody(
                dbc.Button(
                    [
                        html.Img(
                            src=icon_src,
                            alt=text,
                            style={"width": "24px", "height": "24px", "marginRight": "12px"},
                        ),
                        html.Span(text, style={"color": "#9c9c9c", "fontSize": "16px", "fontWeight": "400"}),
                    ],
                    id={"type": "sidebar-dropdown-toggle", "index": dropdown_id},
                    color="link",
                    className="sidebar-dropdown-toggle-button",
                    style={
                        "backgroundColor": "transparent",
                        "display": "flex",
                        "alignItems": "center",
                        "padding": f"{horizontal_padding}px {vertical_padding}px",
                        "borderRadius": "8px",
                    },
                ),
                className="sidebar-dropdown-header",
            ),
            dbc.Collapse(
                dbc.CardBody(
                    dropdown_links,
                    className="sidebar-dropdown-content",
                    style={"borderRadius": "0 0 8px 8px"},
                ),
                id={"type": "sidebar-dropdown-content", "index": dropdown_id},
                is_open=False,
            ),
        ],
        id={"type": "sidebar-dropdown-container", "index": dropdown_id},
        color="dark",
        outline=False,
        style={"backgroundColor": "transparent", "border": "none", "borderRadius": "8px", "marginBottom": "8px"},
    )


# Top bar with logos and navigation links
topbar = dbc.Navbar(
    [
        # Left section with hamburger menu and logos
        html.Div(
            [
                dbc.Button(
                    html.I(className="fas fa-bars sidebar-toggle-icon"),
                    id="sidebar-toggle",
                    color="link",
                    size="sm",
                    style={
                        "color": "#9c9c9c",
                        "fontSize": "18px",
                        "padding": "8px 12px",
                        "marginRight": "15px",
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
                        "marginRight": "15px",
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
                        "display": "inline-block",
                        "verticalAlign": "middle",
                    },
                ),
            ],
            className="navbar-brand-section",
            style={
                "display": "flex",
                "alignItems": "center",
                "flex": "0 0 auto",
            },
        ),
        # Middle section with navigation links - centered
        html.Div(
            dbc.Nav(
                [
                    dbc.NavItem(
                        dbc.NavLink(
                            "Welcome",
                            href="/",
                            external_link=True,
                            target="_self",
                            style={
                                "color": "#9c9c9c",
                                "fontSize": "16px",
                                "padding": "8px 20px",
                                "textDecoration": "none",
                                "borderRadius": "8px",
                                "lineHeight": "1.2",
                            },
                        )
                    ),
                    dbc.NavItem(
                        dbc.NavLink(
                            "Visualizations",
                            href="/repo_overview",
                            active="exact",
                            style={
                                "backgroundColor": "transparent",
                                "border": "none",
                                "color": "#9c9c9c",
                                "fontSize": "16px",
                                "padding": "8px 20px",
                                "borderRadius": "8px",
                                "textDecoration": "none",
                                "lineHeight": "1.2",
                            },
                        )
                    ),
                ],
                className="navbar-main-navigation",
                navbar=True,
                style={"gap": "0px"},
            ),
            className="navbar-navigation-section",
            style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "flex": "1 1 auto",
            },
        ),
        # Right section - empty spacer for balance
        html.Div(
            style={
                "flex": "0 0 auto",
                "width": "200px",  # Match approximate width of left section
            },
        ),
    ],
    id="rectangular-bar",
    color="#1D1D1D",
    dark=True,
    style={
        "height": "60px",
        "border-bottom": "1.5px solid #292929",
        "padding": "0 20px",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
    },
)


#  login banner that will be displayed when login is disabled
login_banner = None
if os.getenv("AUGUR_LOGIN_ENABLED", "False") != "True":
    login_banner = dbc.Alert(
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
            "position": "fixed",
            "top": "70px",
            "right": "20px",
            "zIndex": "1000",
        },
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
        dbc.Alert(
            [
                html.I(className="quota-warning-icon"),  # Warning icon
                "Browser storage limit reached. Search will use a reduced cache which may slightly impact performance. All features will still work normally.",
            ],
            id="storage-quota-warning",  # ID used by Javascript to show/hide this alert
            color="warning",
            dismissable=True,
            style={"display": "none", "marginBottom": "12px"},  # Initially hidden, controlled by JavaScript
            className="search-storage-warning",
        ),
        # Main search input with proper dropdown positioning
        html.Div(
            dbc.InputGroup(
                [
                    dbc.InputGroupText(
                        html.I(className="fas fa-search"),
                        style={
                            "backgroundColor": "#323232",
                            "border": "1px solid #484848",
                            "borderRight": "none",
                            "borderRadius": "12px 0 0 12px",
                            "fontSize": "14px",
                            "color": "#9c9c9c",
                            "height": "42px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "width": "42px",
                            "minWidth": "42px",
                            "maxWidth": "42px",  # Prevent icon area from expanding
                            "flex": "0 0 42px",  # Fixed flex basis
                        },
                    ),
                    dmc.MultiSelect(
                        id="projects",
                        searchable=True,
                        clearable=True,
                        nothingFound="No matching repos/orgs.",
                        placeholder="Search repos & orgs...",  # Shorter placeholder
                        variant="filled",
                        debounce=100,
                        data=[augur.initial_multiselect_option()],
                        value=[augur.initial_multiselect_option()["value"]],
                        className="search-multiselect-input",
                        style={
                            "width": "320px",  # Fixed width to prevent wrapping
                            "minWidth": "320px",  # Same as width for consistency
                            "maxWidth": "320px",  # Lock the width
                            "flex": "0 0 320px",  # Fixed flex basis
                        },
                        styles={
                            "input": {
                                "fontSize": "14px",
                                "height": "42px",
                                "padding": "0 8px",  # Reduced padding for tighter fit
                                "borderRadius": "0 12px 12px 0",
                                "display": "flex",
                                "alignItems": "center",
                                "backgroundColor": "#323232",
                                "borderColor": "#484848",
                                "borderLeft": "none",
                                "color": "#ffffff",
                                "fontWeight": "400",
                                "width": "320px !important",  # Fixed width
                                "minWidth": "320px !important",  # Same as width
                                "maxWidth": "320px !important",  # Lock the width
                                "flex": "0 0 320px !important",  # Fixed flex basis
                            },
                            "dropdown": {
                                "borderRadius": "8px",
                                "backgroundColor": "#323232",
                                "border": "1px solid #484848",
                                "boxShadow": "0 4px 16px rgba(0, 0, 0, 0.4)",
                                "zIndex": 1000,
                                "width": "368px",  # Fixed width to match container
                                "minWidth": "368px",  # Prevent shrinking
                                "maxWidth": "368px",  # Prevent expansion
                                "position": "absolute",  # Use absolute positioning for overlay
                                "marginTop": "2px",  # Small gap between input and dropdown
                                "left": "0",  # Align with parent left
                                "top": "100%",  # Position below input
                                "contain": "layout style paint",  # CSS containment
                            },
                            "item": {
                                "borderRadius": "6px",
                                "margin": "2px 4px",
                                "color": "#ffffff",
                                "fontSize": "13px",
                                "padding": "8px 12px",
                                "whiteSpace": "nowrap",  # Prevent text wrapping
                                "overflow": "hidden",  # Hide overflow
                                "textOverflow": "ellipsis",  # Add ellipsis for very long text
                                "lineHeight": "1.4",
                            },
                            "value": {
                                "backgroundColor": "#404040",
                                "color": "#ffffff",
                                "borderRadius": "6px",
                                "fontSize": "11px",  # Smaller font for selected values
                                "maxWidth": "120px",  # Reduced width for selected values
                                "overflow": "hidden",
                                "textOverflow": "ellipsis",
                                "whiteSpace": "nowrap",  # Prevent text wrapping
                                "display": "inline-block",  # Ensure proper inline behavior
                                "margin": "2px",  # Reduced margin
                            },
                            "searchInput": {
                                "fontSize": "14px",
                                "color": "#ffffff",
                                "backgroundColor": "transparent",
                            },
                        },
                    ),
                    dbc.Button(
                        html.I(className="fas fa-search", style={"display": "none"}),
                        id="search",
                        n_clicks=0,
                        size="sm",
                        color="outline-secondary",
                        title="Search",
                        style={"display": "none"},  # Hidden since we have InputGroupText now
                    ),
                ],
                style={
                    "marginBottom": "16px",
                    "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.15)",
                    "width": "368px",  # Fixed total width (42px icon + 320px input + 6px gap)
                    "minWidth": "368px",  # Prevent shrinking
                    "maxWidth": "368px",  # Prevent expansion
                    "boxSizing": "border-box",  # Include padding/border in width calculation
                    "display": "flex",  # Use flexbox for stable layout
                    "alignItems": "stretch",  # Ensure all children have same height
                    "flexWrap": "nowrap",  # Prevent wrapping
                },
            ),
            style={
                "position": "relative",  # Enable positioning context
                "zIndex": 10,  # Ensure dropdown appears above other elements
                "overflow": "visible",  # Allow dropdown to extend
                "width": "368px",  # Fixed width to match InputGroup
                "minWidth": "368px",  # Prevent shrinking
                "maxWidth": "368px",  # Prevent expansion
                "boxSizing": "border-box",  # Include padding/border in width calculation
            },
        ),
        # Compact action buttons with better spacing
        html.Div(
            [
                dbc.ButtonGroup(
                    [
                        dbc.Button(
                            html.I(className="fas fa-question-circle"),
                            id="search-help",
                            n_clicks=0,
                            size="sm",
                            color="outline-secondary",
                            title="Search Help",
                            style={
                                "backgroundColor": "transparent",
                                "border": "1px solid #484848",
                                "borderRadius": "6px",
                                "padding": "4px 8px",
                                "fontSize": "12px",
                                "color": "#9c9c9c",
                                "width": "36px",
                                "height": "28px",
                            },
                        ),
                        dbc.Button(
                            html.I(className="fas fa-list"),
                            id="repo-list-button",
                            n_clicks=0,
                            size="sm",
                            color="outline-secondary",
                            title="Repository List",
                            style={
                                "backgroundColor": "transparent",
                                "border": "1px solid #484848",
                                "borderRadius": "6px",
                                "padding": "4px 8px",
                                "fontSize": "12px",
                                "color": "#9c9c9c",
                                "width": "36px",
                                "height": "28px",
                            },
                        ),
                    ],
                    style={"gap": "6px"},
                ),
                # Bot filter switch with clean design
                html.Div(
                    dbc.Switch(
                        id="bot-switch",
                        label="Bot Filter",
                        value=True,
                        input_class_name="botlist-filter-switch",
                        style={
                            "fontSize": "13px",
                            "color": "#9c9c9c",
                            "fontWeight": "400",
                        },
                    ),
                    style={"marginTop": "12px"},
                ),
            ],
            style={"marginBottom": "16px"},
        ),
        # Alerts section with minimal styling
        dbc.Alert(
            children="Please ensure that your spelling is correct. "
            "If your selection definitely isn't present, please request that "
            'it be loaded using the help button "REPO/ORG Request" '
            "in the bottom right corner of the screen.",
            id="help-alert",
            dismissable=True,
            fade=True,
            is_open=False,
            color="info",
            style={
                "marginBottom": "12px",
                "fontSize": "13px",
                "padding": "8px 12px",
            },
        ),
        dbc.Alert(
            children="List of repos",
            id="repo-list-alert",
            dismissable=True,
            fade=True,
            is_open=False,
            color="light",
            style={
                "overflow-y": "scroll",
                "max-height": "300px",
                "marginBottom": "0px",
                "fontSize": "13px",
                "padding": "8px 12px",
            },
        ),
    ],
    className="search-container",
    style={
        "padding": "20px 8px 16px 8px",  # Further reduced padding for single line fit
        "backgroundColor": "transparent",
        "overflow": "visible",  # Allow dropdown to extend beyond container
        "position": "relative",  # Enable proper positioning context
        "width": "100%",  # Use full container width
        "maxWidth": "100%",  # Ensure container doesn't exceed sidebar width
        "boxSizing": "border-box",  # Include padding in width calculation
        "contain": "layout",  # CSS containment for better layout control
    },
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
            login_banner or html.Div(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            topbar,
                            # Main layout with improved flexbox structure
                            html.Div(
                                [
                                    # Left sidebar with dbc.Collapse
                                    dbc.Collapse(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    search_bar,
                                                    # Navigation menu
                                                    dbc.Nav(
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
                                                        vertical=True,
                                                        pills=True,
                                                        className="sidebar-navigation-menu",
                                                    ),
                                                ],
                                                className="sidebar-content-body",
                                                style={"overflow": "visible"},  # Allow dropdown to be visible
                                            ),
                                            color="dark",
                                            outline=False,
                                            style={
                                                "width": "450px",
                                                "minWidth": "450px",
                                                "background-color": "#1D1D1D",
                                                "border-radius": "12px 0 0 12px",
                                                "border-right": "1.5px solid #292929",
                                                "border": "none",
                                                "height": "calc(100vh - 60px - 56px - 4px)",
                                                "overflow-y": "auto",
                                                "overflow-x": "visible",  # Allow dropdown to be fully visible
                                            },
                                        ),
                                        id="sidebar-collapse",
                                        is_open=False,  # Start with sidebar collapsed
                                        dimension="width",  # Collapse horizontally
                                        className="sidebar-collapse-container",
                                        style={"overflow": "visible"},  # Allow dropdown to be visible
                                    ),
                                    # Main content area with flex-grow
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                dcc.Loading(
                                                    children=[
                                                        html.Div(
                                                            id="results-output-container",
                                                            className="results-output-section",
                                                        )
                                                    ],
                                                    color="#119DFF",
                                                    type="dot",
                                                    fullscreen=True,
                                                ),
                                                dcc.Loading(
                                                    dbc.Badge(
                                                        children="Data Loaded",
                                                        id="data-badge",
                                                        color="#0F5880",
                                                        className="data-status-badge",
                                                        style={"marginBottom": ".5%"},
                                                    ),
                                                    type="cube",
                                                    color="#0F5880",
                                                ),
                                                dash.page_container,
                                            ],
                                            className="main-content-body",
                                        ),
                                        id="page-container",
                                        color="dark",
                                        outline=False,
                                        style={
                                            "background-color": "#1D1D1D",
                                            "border": "none",
                                            "borderRadius": "0 12px 12px 0",
                                            "height": "calc(100vh - 60px - 56px - 4px)",
                                            "flex": "1",
                                            "minWidth": "0",  # Allow flex shrinking
                                            "overflow-y": "auto",
                                        },
                                        className="main-content-container",
                                    ),
                                ],
                                id="main-layout-container",
                                className="main-layout-flexbox",
                                style={
                                    "display": "flex",
                                    "height": "calc(100vh - 60px - 56px - 4px)",
                                    "gap": "0px",
                                    "alignItems": "stretch",
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
        className="app-main-container",
        style={
            "background-color": "#242424",
        },
    ),
    style={"background-color": "#242424", "min-height": "100vh", "margin": "0", "padding": "0"},
)
