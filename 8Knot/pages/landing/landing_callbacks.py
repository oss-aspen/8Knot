from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

# Import welcome sections for tab content
try:
    from .sections.how_8knot_works_page1 import layout as general_tab_page1
    from .sections.how_8knot_works_page2 import layout as general_tab_page2
    from .sections.plotly_section import layout as plotly_tab_contents
    from .sections.augur_login_section import layout as augur_tab_contents
    from .sections.user_group_section import layout as group_tab_contents
    from .sections.definitions_section import layout as definitions_tab_contents
except ImportError:
    # Fallback if sections don't exist
    general_tab_page1 = html.Div("General section page 1 not available")
    general_tab_page2 = html.Div("General section page 2 not available")
    plotly_tab_contents = html.Div("Plotly section not available")
    augur_tab_contents = html.Div("Augur section not available")
    group_tab_contents = html.Div("User group section not available")
    definitions_tab_contents = html.Div("Definitions section not available")

# Create the How 8Knot Works tab with two pages
def create_how_8knot_works_content():
    """Create the How 8Knot Works tab with left sidebar navigation using DBC components."""
    return dbc.Container(
        [
            dbc.Row(
                [
                    # Left sidebar with vertical navigation
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            dbc.Stack(
                                                [
                                                    dbc.Button(
                                                        "8Knot Pages",
                                                        id="page-1-btn",
                                                        className="page-nav-btn page-nav-btn-active",
                                                        n_clicks=0,
                                                        outline=False,
                                                        color="secondary",
                                                        size="sm",
                                                    ),
                                                    dbc.Button(
                                                        "How 8Knot Works",
                                                        id="page-2-btn",
                                                        className="page-nav-btn page-nav-btn-inactive",
                                                        n_clicks=0,
                                                        outline=True,
                                                        color="secondary",
                                                        size="sm",
                                                    ),
                                                ],
                                                direction="vertical",
                                                gap=3,
                                            )
                                        ],
                                        className="p-3",
                                    )
                                ],
                                className="sidebar-navigation h-100",
                            )
                        ],
                        width=12,
                        lg=3,
                        className="mb-3 mb-lg-0",
                    ),
                    # Main content area
                    dbc.Col(
                        [
                            html.Div(
                                id="page-content",
                                className="page-content",
                                children=[general_tab_page1],  # Default to page 1
                            ),
                        ],
                        width=12,
                        lg=9,
                    ),
                ],
                className="g-3",
            )
        ],
        fluid=True,
        className="two-page-container",
    )


general_tab_contents = create_how_8knot_works_content()

# Landing Page Callbacks

# Callback to handle Learn button and show/hide welcome content
@callback(
    [
        Output("welcome-content", "className"),
        Output("learn-button-icon", "className"),
        Output("welcome-content-state", "data"),
    ],
    Input("learn-button", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_welcome_content(n_clicks):
    """Toggle the visibility of welcome content and rotate the button icon."""
    if n_clicks and n_clicks > 0:
        # Determine current state (assuming it starts collapsed)
        is_expanded = (n_clicks % 2) == 1

        if is_expanded:
            # Show the welcome content with animation
            content_class = "landing-welcome-content how-8knot-works-section landing-welcome-content--visible landing-welcome-content--entering"
            icon_class = "fas fa-chevron-up landing-button-icon landing-button-icon--rotated"
        else:
            # Hide the welcome content
            content_class = "landing-welcome-content how-8knot-works-section"
            icon_class = "fas fa-chevron-down landing-button-icon"

        return content_class, icon_class, {"expanded": is_expanded}

    # Default state (hidden)
    return (
        "landing-welcome-content how-8knot-works-section",
        "fas fa-chevron-down landing-button-icon",
        {"expanded": False},
    )


# Note: Animation handling is now done via CSS classes in the main callback above


# Callback to handle page navigation within How 8Knot Works tab
@callback(
    [
        Output("page-content", "children"),
        Output("page-1-btn", "className"),
        Output("page-2-btn", "className"),
        Output("page-1-btn", "outline"),
        Output("page-2-btn", "outline"),
    ],
    [
        Input("page-1-btn", "n_clicks"),
        Input("page-2-btn", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def update_page_content(page1_clicks, page2_clicks):
    """Update the page content within How 8Knot Works tab using DBC button states."""
    # Determine which button was clicked most recently
    if page1_clicks is None:
        page1_clicks = 0
    if page2_clicks is None:
        page2_clicks = 0

    # Show page 2 if page 2 button was clicked more recently and at least once
    if page2_clicks > 0 and page2_clicks >= page1_clicks:
        return (
            general_tab_page2,
            "page-nav-btn page-nav-btn-inactive",  # page 1 inactive
            "page-nav-btn page-nav-btn-active",  # page 2 active
            True,  # page 1 outline (inactive)
            False,  # page 2 solid (active)
        )
    else:
        return (
            general_tab_page1,
            "page-nav-btn page-nav-btn-active",  # page 1 active
            "page-nav-btn page-nav-btn-inactive",  # page 2 inactive
            False,  # page 1 solid (active)
            True,  # page 2 outline (inactive)
        )


# Callback to handle DBC tab switching and update content
@callback(
    [
        Output("tab-content-main", "children"),
        Output("current-tab-title", "children"),
    ],
    Input("welcome-tabs", "active_tab"),
    prevent_initial_call=False,
)
def update_tab_content(active_tab):
    """Update the main content and side navigation title based on the selected DBC tab."""
    tab_content_map = {
        "plotlyfiguretools": (plotly_tab_contents, "Using 8Knot Visualizations"),
        "general": (general_tab_contents, "How 8Knot Works"),
        "auguraccount": (augur_tab_contents, "Logging into Augur"),
        "usergroup": (group_tab_contents, "Creating Group Projects"),
        "definitions": (definitions_tab_contents, "Definitions"),
    }

    content, title = tab_content_map.get(active_tab, (plotly_tab_contents, "Using 8Knot Visualizations"))
    return content, title
