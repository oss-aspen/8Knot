from dash import html, dcc
import dash
import dash_bootstrap_components as dbc

# Import welcome sections for tabs
try:
    from .sections.general_section import layout as general_tab_contents
    from .sections.plotly_section import layout as plotly_tab_contents
    from .sections.augur_login_section import layout as augur_tab_contents
    from .sections.user_group_section import layout as group_tab_contents
except ImportError:
    # Fallback if sections don't exist
    general_tab_contents = html.Div("General section not available")
    plotly_tab_contents = html.Div("Plotly section not available")
    augur_tab_contents = html.Div("Augur section not available")
    group_tab_contents = html.Div("User group section not available")

# Register this as the main landing page
dash.register_page(__name__, path="/", order=1, title="Welcome")


def create_landing_hero():
    """Create the main hero section with 8Knot logo and title."""
    return html.Div(
        className="landing-hero",
        children=[
            # Logo section
            html.Div(
                className="landing-logo-section",
                children=[
                    html.Img(
                        src="/assets/8Knot.svg",
                        alt="8Knot Logo",
                        className="landing-logo",
                    ),
                    html.H1(
                        "Advanced open-source project analysis by Augur",
                        className="landing-title",
                    ),
                    html.P(
                        "8Knot hosts advanced analysis of open source projects, enriching the study of communities for community architects, developers, and Business Intelligence experts alike.",
                        className="landing-subtitle",
                    ),
                ],
            ),
            # Learn button section
            html.Div(
                className="landing-cta-section",
                children=[
                    html.P(
                        "Is this your first time here?",
                        className="landing-cta-text",
                    ),
                    dbc.Button(
                        [
                            "Learn how 8Knot works ",
                            html.I(
                                id="learn-button-icon",
                                className="fas fa-chevron-down landing-button-icon",
                            ),
                        ],
                        id="learn-button",
                        className="landing-learn-button",
                        color="light",
                    ),
                ],
            ),
        ],
    )


def create_welcome_content():
    """Create the expandable welcome content section with tabs."""
    return html.Div(
        id="welcome-content",
        className="landing-welcome-content",
        children=[
            dbc.Container(
                [
                    html.H2(
                        "Welcome to 8Knot",
                        className="landing-welcome-title",
                    ),
                    dcc.Tabs(
                        id="welcome-tabs",
                        value="plotlyfiguretools",
                        className="landing-tabs",
                        children=[
                            dcc.Tab(
                                label="Using 8Knot Visualizations",
                                value="plotlyfiguretools",
                                children=[plotly_tab_contents],
                                className="landing-tab",
                                selected_className="landing-tab landing-tab--selected",
                            ),
                            dcc.Tab(
                                label="How 8Knot Works",
                                value="general",
                                children=[general_tab_contents],
                                className="landing-tab",
                                selected_className="landing-tab landing-tab--selected",
                            ),
                            dcc.Tab(
                                label="Logging into Augur",
                                value="auguraccount",
                                children=[augur_tab_contents],
                                className="landing-tab",
                                selected_className="landing-tab landing-tab--selected",
                            ),
                            dcc.Tab(
                                label="Creating Project Groups",
                                value="usergroup",
                                children=[group_tab_contents],
                                className="landing-tab",
                                selected_className="landing-tab landing-tab--selected",
                            ),
                        ],
                    ),
                ],
                fluid=True,
                className="landing-tab-content",
            )
        ],
    )


# Main layout for the landing page
layout = html.Div(
    className="landing-page",
    children=[
        create_landing_hero(),
        create_welcome_content(),
        # Store to track welcome content state
        dcc.Store(id="welcome-content-state", data={"expanded": False}),
    ],
)
