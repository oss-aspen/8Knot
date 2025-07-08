import dash
from dash import callback, Input, Output, State
from dash.dependencies import Input, Output, State


# Dash callback for sidebar toggle
@dash.callback(
    [
        Output("sidebar-card", "style"),
        Output("sidebar-card", "className"),
        Output("sidebar-full-content", "style"),
        Output("repo-overview-text", "style"),
        Output("contributions-text", "style"),
        Output("contributors-text", "style"),
        Output("affiliation-text", "style"),
        Output("chaoss-text", "style"),
        Output("main-card", "style"),
        Output("sidebar-toggle-icon", "className"),
        Output("sidebar-collapsed", "data"),
        Output("contributors-dropdown-content", "style", allow_duplicate=True),
        Output("contributors-dropdown-icon", "className", allow_duplicate=True),
        Output("contributors-dropdown-open", "data", allow_duplicate=True),
        Output("contributors-dropdown-wrapper", "className", allow_duplicate=True),
        Output("dummy-search-navlink", "style"),
    ],
    [
        Input("sidebar-toggle-btn", "n_clicks"),
        Input("contributors-dropdown-toggle", "n_clicks"),
        Input("dummy-search-navlink", "n_clicks"),
    ],
    [State("sidebar-collapsed", "data"), State("contributors-dropdown-open", "data")],
    prevent_initial_call=True,
)
def toggle_sidebar(toggle_n, contributors_n, dummy_search_n, collapsed, contributors_open):
    # SEARCH ICON POSITIONING CONSTANT - Adjust this value to move search icon left/right
    SEARCH_ICON_LEFT_ADJUSTMENT = -15  # Negative values move left, positive values move right

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # If contributors dropdown was clicked, always expand sidebar and toggle dropdown
    if trigger_id == "contributors-dropdown-toggle":
        collapsed = False  # Force expand
        contributors_open = not contributors_open
    # If dummy search navlink was clicked, always expand sidebar
    elif trigger_id == "dummy-search-navlink":
        collapsed = False  # Force expand
        contributors_open = False  # Close contributors dropdown
    # If sidebar toggle was clicked, toggle sidebar state
    elif trigger_id == "sidebar-toggle-btn":
        collapsed = not collapsed
        # When collapsing, close contributors dropdown
        if collapsed:
            contributors_open = False

    # Calculate centering for collapsed sidebar
    collapsed_sidebar_width = 100  # px
    search_icon_width = 60  # px (including border)
    regular_icon_width = 30  # px

    # For search icon: center the 60px circle in 100px sidebar, shifted left
    search_horizontal_padding = (collapsed_sidebar_width - search_icon_width) // 2 - 8  # Subtract 8px to shift left

    # For regular icons: center in 100px sidebar, shifted left more
    regular_horizontal_padding = (collapsed_sidebar_width - regular_icon_width) // 2 - 15  # Subtract 15px to shift left

    # Text visibility style
    text_style = {"display": "none"} if collapsed else {"display": "inline"}

    # Full content visibility style
    full_content_style = {"display": "none"} if collapsed else {"display": "block"}

    sidebar_style = {
        "borderRadius": "14px 0 0 14px",
        "width": "100px" if collapsed else "340px",
        "background": "#1D1D1D",
        "color": "#fff",
        "padding": f"32px {regular_horizontal_padding}px 32px {regular_horizontal_padding}px"
        if collapsed
        else "32px 18px 32px 18px",
        "boxShadow": "none",
        "border": "none",
        "borderRight": "1px solid #404040",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start",
        "margin": "0px",  # Remove all margins, spacing handled by container padding
        "zIndex": 2,
        "overflow": "hidden",
        "flex": "0 0 auto",  # Don't grow or shrink
    }

    main_style = {
        "borderRadius": "0 14px 14px 0",
        "padding": "0px 40px 40px 40px",
        "margin": "0px",  # Remove all margins, spacing handled by container padding
        "boxShadow": "none",
        "border": "none",
        "background": "#1D1D1D",
        "overflowY": "auto",
        "overflowX": "hidden",
        "display": "flex",
        "flexDirection": "column",
        "marginLeft": "0",
        "flex": "1",  # Grow to fill remaining space
    }

    icon = "fas fa-chevron-right" if collapsed else "fas fa-chevron-left"

    # Contributors dropdown styling
    if contributors_open:
        dropdown_content_style = {"display": "block", "paddingTop": "4px", "borderRadius": "0 0 8px 8px"}
        dropdown_icon_class = "bi bi-chevron-up"
        dropdown_wrapper_class = "dropdown-open"
    else:
        dropdown_content_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
        dropdown_icon_class = "bi bi-chevron-down"
        dropdown_wrapper_class = ""

    # Dummy search navlink styling - only show when collapsed
    dummy_search_style = {
        "display": "flex" if collapsed else "none",
        "alignItems": "center",
        "padding": f"12px {search_horizontal_padding}px" if collapsed else "12px 16px",
        "marginBottom": "24px",  # More spacing before next navlink
        "marginTop": "-40px",  # Move up relative to sidebar
        "marginLeft": f"{SEARCH_ICON_LEFT_ADJUSTMENT}px" if collapsed else "0",  # Adjustable positioning
        "borderRadius": "0" if collapsed else "12px",  # No rounded highlight when collapsed
        "color": "#B0B0B0",
        "textDecoration": "none",
        "fontSize": "16px",
        "fontWeight": 400,
        "transition": "background-color 0.2s ease",
    }

    # Sidebar className based on collapsed state
    sidebar_class = "sidebar-card collapsed" if collapsed else "sidebar-card"

    return (
        sidebar_style,
        sidebar_class,
        full_content_style,
        text_style,
        text_style,
        text_style,
        text_style,
        text_style,
        main_style,
        icon,
        collapsed,
        dropdown_content_style,
        dropdown_icon_class,
        contributors_open,
        dropdown_wrapper_class,
        dummy_search_style,
    )


# Simplified callback for navigation links (just closes dropdown)
@dash.callback(
    [
        Output("contributors-dropdown-content", "style", allow_duplicate=True),
        Output("contributors-dropdown-icon", "className", allow_duplicate=True),
        Output("contributors-dropdown-open", "data", allow_duplicate=True),
        Output("contributors-dropdown-wrapper", "className", allow_duplicate=True),
    ],
    [
        Input("repo-overview-navlink", "n_clicks"),
        Input("contributions-navlink", "n_clicks"),
        Input("affiliation-navlink", "n_clicks"),
        Input("chaoss-navlink", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def close_dropdown_on_navigation(repo_clicks, contrib_clicks, aff_clicks, chaoss_clicks):
    """Close contributors dropdown when any navigation link is clicked"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    # Close dropdown
    dropdown_content_style = {"display": "none", "height": 0, "overflow": "hidden", "padding": 0, "border": 0}
    dropdown_icon_class = "bi bi-chevron-down"
    dropdown_wrapper_class = ""

    return dropdown_content_style, dropdown_icon_class, False, dropdown_wrapper_class
