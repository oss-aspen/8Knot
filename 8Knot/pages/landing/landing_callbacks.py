from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

# Import welcome sections for tab content
try:
    from .sections.pages_overview_section import layout as general_tab_contents
    from .sections.plotly_section import layout as plotly_tab_contents
    from .sections.how_8knot_works_section import layout as how_8knot_works_tab_contents
    from .sections.definitions_section import layout as definitions_tab_contents

    # Keeping for future use

    # from .sections.augur_login_section import layout as augur_tab_contents
    # from .sections.user_group_section import layout as group_tab_contents
except ImportError:
    # Fallback if sections don't exist
    general_tab_contents = html.Div("General section not available")
    plotly_tab_contents = html.Div("Plotly section not available")
    how_8knot_works_tab_contents = html.Div("How 8knot works section not available")
    definitions_tab_contents = html.Div("Definitions section not available")
    # augur_tab_contents = html.Div("Augur section not available")
    # group_tab_contents = html.Div("User group section not available")


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
