from dash import dcc, html, callback, callback_context
from dash.dependencies import Input, Output
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px

# import other sections
from .sections.general_section import layout as general_tab_contents
from .sections.plotly_section import layout as plotly_tab_contents
from .sections.augur_login_section import layout as augur_tab_contents
from .sections.user_group_section import layout as group_tab_contents

# register the page
dash.register_page(__name__, path="/", order=1)


layout = html.Div(
    className="welcome-page-container",
    children=[
        # Main section with gradients
        html.Div(
            className="welcome-main-section",
            children=[
                # background ellipses
                html.Div(
                    [
                        # Ellipse 1(Pink gradient)
                        html.Div(className="welcome-gradient-ellipse-pink"),
                        # Ellipse 2 (Green gradient)
                        html.Div(className="welcome-gradient-ellipse-green"),
                        # Ellipse 3 (Blue gradient)
                        html.Div(className="welcome-gradient-ellipse-blue"),
                    ]
                ),
                html.Div(
                    className="welcome-content-overlay",
                    children=[
                        # Main content section
                        html.Div(
                            className="welcome-main-content",
                            children=[
                                # Main heading
                                html.H1(
                                    "Advanced Open Source Project Analysis by 8Knot",
                                    className="welcome-main-heading",
                                ),
                                # Subtitle
                                html.P(
                                    "8Knot hosts advanced analysis of open source projects, enriching the study of communities for community architects, developers, and Business Intelligence experts alike.",
                                    className="welcome-subtitle",
                                ),
                                # Search bar in the center of the page - COMMENTED OUT
                                # Now using sidebar search bar instead
                                # html.Div(
                                #     style={
                                #         "background": "#292929",
                                #         "borderRadius": "20px",
                                #         "border": "1px solid #C7C7C7",
                                #         "padding": "8px 16px",
                                #         "width": "472px",
                                #         "height": "48px",
                                #         "display": "flex",
                                #         "alignItems": "center",
                                #         "justifyContent": "space-between",
                                #         "boxSizing": "border-box",
                                #         "margin": "0 auto",
                                #     },
                                #     children=[
                                #         dmc.MultiSelect(
                                #             id="projects",  # ID matches index_callbacks for functionality
                                #             searchable=True,
                                #             clearable=True,
                                #             placeholder="Search for organization and repositories",
                                #             nothingFound="No matching repos/orgs.",
                                #             variant="unstyled",
                                #             debounce=100,
                                #             data=[
                                #                 {"label": "org: chaoss", "value": "chaoss"}
                                #             ],  # Default CHAOSS
                                #             value=["chaoss"],  # Default CHAOSS
                                #             style={
                                #                 "fontSize": 15,
                                #                 "zIndex": 99999,  # Higher z-index to ensure it's on top of the other elements
                                #                 "border": "none",
                                #                 "width": "100%",
                                #                 "background": "transparent",
                                #                 "color": "#FAFAFA",
                                #             },
                                #             maxDropdownHeight=300,
                                #             dropdownPosition="bottom",  # Force dropdown to go down
                                #             className="landing-searchbar-dropdown",
                                #         ),
                                #     ],
                                # ),
                                # # Search button (hidden, functionality handled by MultiSelect)
                                # dbc.Button(
                                #     "Search",
                                #     id="search",
                                #     size="lg",
                                #     style={
                                #         "display": "none"
                                #     },
                                # ),
                            ],
                        ),
                        # CTA section - now part of the same unified section with gradients
                        html.Div(
                            className="welcome-cta-section",
                            children=[
                                html.P(
                                    "Is this your first time here?",
                                    className="welcome-cta-text",
                                ),
                                dbc.Button(
                                    [
                                        "Learn how 8Knot works ",
                                        html.I(className="fas fa-chevron-down welcome-icon-margin"),
                                    ],
                                    id="learn-button",
                                    color="light",
                                    className="welcome-learn-button",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Welcome content section - initially hidden - this is the section that appears when the learn button is clicked
        html.Div(
            id="welcome-content",
            className="welcome-content-section",
            children=[
                # Section Title
                html.Div(className="welcome-section-title", children=[html.H1("8Knot Documentation")]),
                # Custom Tab Navigation (matching target design)
                html.Div(
                    className="welcome-tabs-container",
                    children=[
                        html.Div(
                            className="welcome-tab-buttons",
                            children=[
                                html.Button(
                                    "Using 8Knot Visualizations",
                                    id="tab-viz",
                                    className="welcome-tab-button welcome-tab-active",
                                    n_clicks=0,
                                ),
                                html.Button(
                                    "How 8Knot Works", id="tab-works", className="welcome-tab-button", n_clicks=0
                                ),
                                html.Button(
                                    "Logging into Augur", id="tab-augur", className="welcome-tab-button", n_clicks=0
                                ),
                                html.Button(
                                    "Creating Project Groups",
                                    id="tab-groups",
                                    className="welcome-tab-button",
                                    n_clicks=0,
                                ),
                            ],
                        ),
                    ],
                ),
                # Content Area
                html.Div(
                    className="welcome-tab-content-area",
                    children=[
                        # Left sidebar
                        html.Div(
                            className="welcome-content-sidebar",
                            children=[
                                html.Div(className="welcome-sidebar-title", children=["8Knot Pages"]),
                                html.Div(className="welcome-sidebar-link", children=["How 8Knot works"]),
                            ],
                        ),
                        # Main content
                        html.Div(
                            id="welcome-main-content",
                            className="welcome-main-content",
                            children=[
                                # Default content - 8Knot Visualizations
                                html.Div(
                                    className="welcome-content-header",
                                    children=[
                                        html.H2("8Knot Visualizations"),
                                        html.P(
                                            "Each page approaches the study of open source communities from a different perspective."
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="welcome-content-grid",
                                    children=[
                                        html.Div(
                                            className="welcome-content-card",
                                            children=[
                                                html.H3("Repo Overview"),
                                                html.P("General information at the repo group and single repo level"),
                                            ],
                                        ),
                                        html.Div(
                                            className="welcome-content-card",
                                            children=[
                                                html.H3("Contributions"),
                                                html.P("General information at the repo group and single repo level"),
                                            ],
                                        ),
                                        html.Div(
                                            className="welcome-content-card",
                                            children=[
                                                html.H3("Contributors"),
                                                html.P("General information at the repo group and single repo level"),
                                            ],
                                        ),
                                        html.Div(
                                            className="welcome-content-card",
                                            children=[
                                                html.H3("CHAOSS"),
                                                html.P("General information at the repo group and single repo level"),
                                            ],
                                        ),
                                        html.Div(
                                            className="welcome-content-card",
                                            children=[
                                                html.H3("Affiliations"),
                                                html.P("General information at the repo group and single repo level"),
                                            ],
                                        ),
                                        html.Div(
                                            className="welcome-content-card",
                                            children=[
                                                html.H3("Info"),
                                                html.P("General information at the repo group and single repo level"),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Store to track if welcome content should be shown
        dcc.Store(id="show-welcome-content", data=False),
        # JavaScript for smooth scrolling to welcome content
        html.Div(id="scroll-trigger", className="welcome-scroll-trigger"),
        html.Script(
            """
                    // Function to observe when welcome content appears and scroll to it
                    function observeWelcomeContent() {
                        console.log('Setting up welcome content observer...');
                        const welcomeContent = document.getElementById('welcome-content');
                        if (welcomeContent) {
                            console.log('Welcome content element found');
                            const observer = new MutationObserver(function(mutations) {
                                mutations.forEach(function(mutation) {
                                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                                        const target = mutation.target;
                                        console.log('Style changed:', target.style.display);
                                        if (target.style.display === 'block') {
                                            console.log('Scrolling to welcome content...');
                                            setTimeout(function() {
                                                target.scrollIntoView({
                                                    behavior: 'smooth',
                                                    block: 'start'
                                                });
                                            }, 300); // Increased delay
                                        }
                                    }
                                });
                            });

                            observer.observe(welcomeContent, {
                                attributes: true,
                                attributeFilter: ['style']
                            });
                        } else {
                            console.log('Welcome content element not found');
                        }
                    }

                    // Start observing when DOM is ready
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', observeWelcomeContent);
                    } else {
                        observeWelcomeContent();
                    }

                    // Also try after a short delay in case of dynamic content
                    setTimeout(observeWelcomeContent, 1000);
                    """
        ),
        # Hidden components for search functionality - REMOVED
        # These components are now handled by the main layout (index_layout.py)
        # to avoid duplicate ID conflicts
        # just as a reminder if we want to add the search bar back in, we need to add it to the main layout (index_layout.py)
    ],
)


# Callback to handle tab switching and content updates
@callback(
    [
        Output("welcome-main-content", "children"),
        Output("tab-viz", "className"),
        Output("tab-works", "className"),
        Output("tab-augur", "className"),
        Output("tab-groups", "className"),
    ],
    [
        Input("tab-viz", "n_clicks"),
        Input("tab-works", "n_clicks"),
        Input("tab-augur", "n_clicks"),
        Input("tab-groups", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def update_tab_content(viz_clicks, works_clicks, augur_clicks, groups_clicks):
    """Update the content and active tab styling based on button clicks."""

    # Determine which tab was clicked
    ctx = callback_context
    if not ctx.triggered:
        # Default to visualizations tab
        active_tab = "viz"
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        active_tab = button_id.split("-")[1]  # Extract tab name from id

    # Set active classes
    viz_class = "welcome-tab-button welcome-tab-active" if active_tab == "viz" else "welcome-tab-button"
    works_class = "welcome-tab-button welcome-tab-active" if active_tab == "works" else "welcome-tab-button"
    augur_class = "welcome-tab-button welcome-tab-active" if active_tab == "augur" else "welcome-tab-button"
    groups_class = "welcome-tab-button welcome-tab-active" if active_tab == "groups" else "welcome-tab-button"

    # Generate content based on active tab
    if active_tab == "viz":
        content = [
            html.Div(
                className="welcome-content-header",
                children=[
                    html.H2("8Knot Visualizations"),
                    html.P("Each page approaches the study of open source communities from a different perspective."),
                ],
            ),
            html.Div(
                className="welcome-content-grid",
                children=[
                    html.Div(
                        className="welcome-content-card",
                        children=[
                            html.H3("Repo Overview"),
                            html.P("General information at the repo group and single repo level"),
                        ],
                    ),
                    html.Div(
                        className="welcome-content-card",
                        children=[
                            html.H3("Contributions"),
                            html.P("General information at the repo group and single repo level"),
                        ],
                    ),
                    html.Div(
                        className="welcome-content-card",
                        children=[
                            html.H3("Contributors"),
                            html.P("General information at the repo group and single repo level"),
                        ],
                    ),
                    html.Div(
                        className="welcome-content-card",
                        children=[
                            html.H3("CHAOSS"),
                            html.P("General information at the repo group and single repo level"),
                        ],
                    ),
                    html.Div(
                        className="welcome-content-card",
                        children=[
                            html.H3("Affiliations"),
                            html.P("General information at the repo group and single repo level"),
                        ],
                    ),
                    html.Div(
                        className="welcome-content-card",
                        children=[
                            html.H3("Info"),
                            html.P("General information at the repo group and single repo level"),
                        ],
                    ),
                ],
            ),
        ]
    elif active_tab == "works":
        content = [
            html.Div(
                className="welcome-content-header",
                children=[
                    html.H2("How 8Knot Works"),
                    html.P(
                        "8Knot is a data science application that uses data from Augur to render visualizations and generate metrics."
                    ),
                ],
            ),
            general_tab_contents,
        ]
    elif active_tab == "augur":
        content = [
            html.Div(
                className="welcome-content-header",
                children=[
                    html.H2("Logging into Augur"),
                    html.P("Connect your Augur account to access personalized features and data."),
                ],
            ),
            augur_tab_contents,
        ]
    elif active_tab == "groups":
        content = [
            html.Div(
                className="welcome-content-header",
                children=[
                    html.H2("Creating Project Groups"),
                    html.P("Organize and manage your repositories into meaningful groups for analysis."),
                ],
            ),
            group_tab_contents,
        ]
    else:
        content = [html.Div("Content loading...")]

    return content, viz_class, works_class, augur_class, groups_class


# Callback to handle Learn button and show/hide welcome content
@callback(
    [Output("welcome-content", "style"), Output("scroll-trigger", "children")],
    Input("learn-button", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_welcome_content(n_clicks):
    if n_clicks:
        # Show the welcome content when button is clicked - use flex for more flow
        # The welcome page implementation for now, is purely based in CSS, so this expands when user clicks the button
        style = {"display": "flex"}
        # Trigger scroll with JavaScript - shorter delay since no gap to bridge
        scroll_script = html.Script(
            f"""
            setTimeout(function() {{
                const welcomeContent = document.getElementById('welcome-content');
                if (welcomeContent) {{
                    console.log('Scrolling to welcome content via callback...');
                    welcomeContent.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }}, 200);
            """
        )
        return style, scroll_script

    return {"display": "none"}, html.Div()
