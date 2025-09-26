from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px


def create_definition_item(term, definition):
    """
    Create a standardized definition item for the definitions section.

    Args:
        term (str): The term being defined
        definition (str): The definition/explanation of the term

    Returns:
        dbc.Row: A formatted row containing the term and definition
    """
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Div(
                        [
                            html.H3(
                                term,
                                className="section-title",
                            ),
                            html.P(
                                definition,
                                className="feature-body",
                            ),
                        ],
                        className="feature-title",
                    ),
                ],
                width=12,
            )
        ],
        className="feature-section mb-4",
    )


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Definitions", className="main-title"),
                        html.P(
                            "Understanding key terms and concepts used throughout 8Knot will help you better interpret the visualizations and metrics.",
                            className="body-text",
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
                        create_definition_item(
                            "Contributors",
                            "Individuals who make contributions to a repository through commits, pull requests, issues, or other forms of participation.",
                        ),
                        create_definition_item(
                            "Contributions",
                            "Actions taken by contributors including commits, pull requests, issues, code reviews, and other activities that add value to the project.",
                        ),
                        create_definition_item(
                            "Repository",
                            "A storage location for project files, including source code, documentation, and version history. In 8Knot, repositories are the primary unit of analysis.",
                        ),
                        create_definition_item(
                            "CHAOSS",
                            "Community Health Analytics for Open Source Software. A Linux Foundation project focused on creating analytics and metrics to help define community health and sustainability for open source projects.",
                        ),
                        create_definition_item(
                            "Augur",
                            "The data collection and processing system that powers 8Knot. Augur gathers data from various sources including Git repositories, GitHub, GitLab, and other platforms to create comprehensive datasets for analysis.",
                        ),
                        create_definition_item(
                            "User Groups",
                            "Custom collections of repositories and organizations that users can create to analyze related projects together. User groups allow for comparative analysis and tracking of multiple projects as a cohesive unit.",
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
