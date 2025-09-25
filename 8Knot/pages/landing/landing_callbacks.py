from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

# Import welcome sections for tab content
try:
    from .sections.pages_overview_section import layout as general_tab_contents
    from .sections.plotly_section import layout as plotly_tab_contents
    from .sections.how_8knot_works_section import layout as how_8knot_works_tab_contents
    from .sections.definitions_section import layout as definitions_tab_contents

    # Keeping for future use
    from .sections.how_8knot_works_architecture import layout as architecture_tab_layout

    # from .sections.augur_login_section import layout as augur_tab_contents
    # from .sections.user_group_section import layout as group_tab_contents
except ImportError:
    # Fallback if sections don't exist
    general_tab_contents = html.Div("General section not available")
    plotly_tab_contents = html.Div("Plotly section not available")
    how_8knot_works_tab_contents = html.Div("How 8knot works section not available")
    definitions_tab_contents = html.Div("Definitions section not available")
    architecture_tab_layout = html.Div("Architecture section not available")
    # augur_tab_contents = html.Div("Augur section not available")
    # group_tab_contents = html.Div("User group section not available")

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
                                                        id="pages-overview-nav-btn",
                                                        className="page-nav-btn page-nav-btn-active",
                                                        n_clicks=0,
                                                        outline=False,
                                                        color="secondary",
                                                        size="sm",
                                                    ),
                                                    dbc.Button(
                                                        "How 8Knot Works",
                                                        id="architecture-nav-btn",
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
                                id="how-8knot-works-content-area",
                                className="page-content",
                                children=[general_tab_page1],  # Default to pages overview
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


# Callback to handle page navigation within How 8Knot Works tab
@callback(
    [
        Output("how-8knot-works-content-area", "children"),
        Output("pages-overview-nav-btn", "className"),
        Output("architecture-nav-btn", "className"),
        Output("pages-overview-nav-btn", "outline"),
        Output("architecture-nav-btn", "outline"),
    ],
    [
        Input("pages-overview-nav-btn", "n_clicks"),
        Input("architecture-nav-btn", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def update_how_8knot_works_content(pages_overview_clicks, architecture_clicks):
    """Update the content area within How 8Knot Works tab based on navigation button clicks."""
    # Determine which button was clicked most recently
    if pages_overview_clicks is None:
        pages_overview_clicks = 0
    if architecture_clicks is None:
        architecture_clicks = 0

    # Show architecture content if architecture button was clicked more recently and at least once
    if architecture_clicks > 0 and architecture_clicks >= pages_overview_clicks:
        return (
            architecture_tab_layout,
            "page-nav-btn page-nav-btn-inactive",  # pages overview inactive
            "page-nav-btn page-nav-btn-active",  # architecture active
            True,  # pages overview outline (inactive)
            False,  # architecture solid (active)
        )
    else:
        return (
            general_tab_page1,
            "page-nav-btn page-nav-btn-active",  # pages overview active
            "page-nav-btn page-nav-btn-inactive",  # architecture inactive
            False,  # pages overview solid (active)
            True,  # architecture outline (inactive)
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
def update_main_tab_content(selected_tab_id):
    """Update the main content and navigation title based on the selected landing page tab."""
    landing_tab_content_mapping = {
        "plotlyfiguretools": (plotly_tab_contents, "Using 8Knot Visualizations"),
        "general": (general_tab_contents, "8Knot Pages"),
        "how8knotworks": (how_8knot_works_tab_contents, "How 8Knot Works"),
        "definitions": (definitions_tab_contents, "Definitions"),
        # "auguraccount": (augur_tab_contents, "Logging into Augur"),
        # "usergroup": (group_tab_contents, "Creating Group Projects"),
    }

    tab_content, tab_title = landing_tab_content_mapping.get(
        selected_tab_id, (plotly_tab_contents, "Using 8Knot Visualizations")
    )
    return tab_content, tab_title
