from dash import Input, Output, callback

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
            content_class = "landing-welcome-content landing-welcome-content--visible landing-welcome-content--entering"
            icon_class = "fas fa-chevron-up landing-button-icon landing-button-icon--rotated"
        else:
            # Hide the welcome content
            content_class = "landing-welcome-content"
            icon_class = "fas fa-chevron-down landing-button-icon"
        
        return content_class, icon_class, {"expanded": is_expanded}
    
    # Default state (hidden)
    return "landing-welcome-content", "fas fa-chevron-down landing-button-icon", {"expanded": False}


# Note: Animation handling is now done via CSS classes in the main callback above
