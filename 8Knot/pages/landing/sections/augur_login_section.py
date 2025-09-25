from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Logging into Augur", className="main-title"),
                        html.P(
                            "There are no 8Knot accounts, exactly. Accounts are created and managed by Augur, and account information is used to enrich the experience of using 8Knot.",
                            className="body-text",
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        # Enhanced visualization section
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H3("Enhanced Visualization Experience", className="section-title"),
                                html.P(
                                    "Once logged in, you'll have access to enhanced features and personalized group management for better data exploration.",
                                    className="feature-body",
                                ),
                            ],
                            className="feature-title",
                        ),
                        html.Div(
                            [
                                html.Img(
                                    src="assets/focus_group.png",
                                    className="feature-image img-fluid",
                                    alt="Interactive focus and zoom capabilities",
                                ),
                                html.P(
                                    "Interactive focus and zoom capabilities",
                                    className="image-caption text-muted small",
                                ),
                            ],
                            className="image-container",
                        ),
                    ],
                    width=12,
                )
            ],
            className="feature-section mb-4",
        ),
        # Login steps section with vertical layout
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        # Step 1 - Register
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3("1. Register for an Augur account", className="section-title"),
                                                html.P(
                                                    'After clicking on "Augur log in/sign up" in the top right corner of the page, you\'ll be redirected to the Augur frontend where you can create an account.',
                                                    className="feature-body",
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/focus_group.png",
                                                    className="feature-image img-fluid",
                                                    alt="Augur Registration Page",
                                                ),
                                                html.P(
                                                    "Augur Registration Page",
                                                    className="image-caption text-muted small",
                                                ),
                                            ],
                                            className="image-container",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section mb-4",
                        ),
                        # Step 2 - Authorize
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3("2. Authorize 8Knot access", className="section-title"),
                                                html.P(
                                                    "Once you've created your account, you'll be redirected to an authorization page. This page requests that you allow 8Knot and Augur to share your account data to enrich your experience.",
                                                    className="feature-body",
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/focus_group.png",
                                                    className="feature-image img-fluid",
                                                    alt="Augur Authorization Page",
                                                ),
                                                html.P(
                                                    "Augur Authorization Page",
                                                    className="image-caption text-muted small",
                                                ),
                                            ],
                                            className="image-container",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section mb-4",
                        ),
                        # Step 3 - Successful Login
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3("3. Successful Login", className="section-title"),
                                                html.P(
                                                    'After authorizing with Augur, new icons should be available, including a panel with your username. "Refresh Groups" will update any group changes made in Augur. "Manage Groups" opens a new Augur tab where you can make changes to your groups.',
                                                    className="feature-body",
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/focus_group.png",
                                                    className="feature-image img-fluid",
                                                    alt="8Knot Logged In Interface",
                                                ),
                                                html.P(
                                                    "8Knot Logged In Interface",
                                                    className="image-caption text-muted small",
                                                ),
                                            ],
                                            className="image-container",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section",
                        ),
                    ]
                )
            ],
            className="section-bordered",
        ),
    ],
    fluid=True,
    className="content-container",
)
