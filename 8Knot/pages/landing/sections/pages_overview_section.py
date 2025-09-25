from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

# First page of How 8Knot Works - Information only
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("8Knot Pages", className="main-title"),
                        html.P(
                            "Each page approaches the study of open source communities from a different perspective.",
                            className="body-text mb-4",
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        # 2x3 Grid using DBC Row/Col
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        # Row 1: Repo Overview, Contributions, Contributors
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H3(
                                                            "Repo Overview",
                                                            className="section-title",
                                                        ),
                                                        html.P(
                                                            "General information at the repo group and single repo level",
                                                            className="section-description",
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100 page-item",
                                        )
                                    ],
                                    width=12,
                                    md=4,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H3(
                                                            "Contributions",
                                                            className="section-title",
                                                        ),
                                                        html.P(
                                                            "Track pull requests, commits, and issue activity across repositories",
                                                            className="section-description",
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100 page-item",
                                        )
                                    ],
                                    width=12,
                                    md=4,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H3(
                                                            "Contributors",
                                                            className="section-title",
                                                        ),
                                                        html.P(
                                                            "Analyze contributor behavior, types, and engagement patterns",
                                                            className="section-description",
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100 page-item",
                                        )
                                    ],
                                    width=12,
                                    md=4,
                                    className="mb-3",
                                ),
                            ],
                            className="mb-3",
                        ),
                        # Row 2: CHAOSS, Affiliations, Info
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H3(
                                                            "CHAOSS",
                                                            className="section-title",
                                                        ),
                                                        html.P(
                                                            "Community health metrics and CHAOSS standard measurements",
                                                            className="section-description",
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100 page-item",
                                        )
                                    ],
                                    width=12,
                                    md=4,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H3(
                                                            "Affiliations",
                                                            className="section-title",
                                                        ),
                                                        html.P(
                                                            "Organization and company affiliations of project contributors",
                                                            className="section-description",
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100 page-item",
                                        )
                                    ],
                                    width=12,
                                    md=4,
                                    className="mb-3",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H3(
                                                            "Info",
                                                            className="section-title",
                                                        ),
                                                        html.P(
                                                            "Additional project information and metadata analysis",
                                                            className="section-description",
                                                        ),
                                                    ]
                                                )
                                            ],
                                            className="h-100 page-item",
                                        )
                                    ],
                                    width=12,
                                    md=4,
                                    className="mb-3",
                                ),
                            ]
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
