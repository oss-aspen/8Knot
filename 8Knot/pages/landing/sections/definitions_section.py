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
                        html.H1("Definitions", className="main-title", style={"font-size": "2.6rem !important"}),
                        html.P(
                            "Understanding key terms and concepts used throughout 8Knot will help you better interpret the visualizations and metrics.",
                            className="body-text",
                            style={"font-size": "1.5rem !important"},
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        # Contributors Definition
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Contributors",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Individuals who make contributions to a repository through commits, pull requests, issues, or other forms of participation.",
                                                    className="feature-body",
                                                    style={"font-size": "1.4rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section mb-4",
                        ),
                        # Contributions Definition
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Contributions",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Actions taken by contributors including commits, pull requests, issues, code reviews, and other activities that add value to the project.",
                                                    className="feature-body",
                                                    style={"font-size": "1.4rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section mb-4",
                        ),
                        # Repository Definition
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Repository",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "A storage location for project files, including source code, documentation, and version history. In 8Knot, repositories are the primary unit of analysis.",
                                                    className="feature-body",
                                                    style={"font-size": "1.4rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section mb-4",
                        ),
                        # CHAOSS Definition
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "CHAOSS",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Community Health Analytics for Open Source Software. A Linux Foundation project focused on creating analytics and metrics to help define community health and sustainability for open source projects.",
                                                    className="feature-body",
                                                    style={"font-size": "1.4rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section mb-4",
                        ),
                        # Augur Definition
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Augur",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "The data collection and processing system that powers 8Knot. Augur gathers data from various sources including Git repositories, GitHub, GitLab, and other platforms to create comprehensive datasets for analysis.",
                                                    className="feature-body",
                                                    style={"font-size": "1.4rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="feature-section mb-4",
                        ),
                        # User Groups Definition
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "User Groups",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Custom collections of repositories and organizations that users can create to analyze related projects together. User groups allow for comparative analysis and tracking of multiple projects as a cohesive unit.",
                                                    className="feature-body",
                                                    style={"font-size": "1.4rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
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
