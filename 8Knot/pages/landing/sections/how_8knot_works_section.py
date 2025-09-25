from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

# How 8knot Works section - showing the architecture image
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("How 8Knot Works", className="main-title"),
                        html.P(
                            "8Knot provides comprehensive analysis of open source project health and community dynamics using Augur's data foundation.",
                            className="body-text mb-4",
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        # Text
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H3("Cloud-native architecture", className="section-title"),
                                        html.P(
                                            "We designed 8Knot to be easily deployable locally but to also scale well in the cloud. On a laptop its a multi-container application. On a container orchestration platform (Openshift, Kubernetes) it's multi-service.",
                                            className="feature-body",
                                        ),
                                    ],
                                )
                            ],
                        )
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H3("Data science first", className="section-title"),
                                        html.P(
                                            "All analytical processing is done with Python data science packages. If a workload is sufficiently complex, we can use distributed computing to handle it. Machine learning and modeling are first-priority workloads.",
                                            className="feature-body",
                                        ),
                                    ],
                                )
                            ],
                        )
                    ],
                    width=6,
                )
            ],
        ),
        # Centered image display
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.Img(
                                            src="assets/8knot_works.png",
                                            className="img-fluid main-feature-image",
                                            alt="8Knot Works Overview",
                                            style={
                                                "width": "100%",
                                                "max-width": "800px",
                                                "height": "auto",
                                            },
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ],
                            className="border-0 bg-transparent section-bordered",
                        )
                    ],
                    width=12,
                    className="d-flex justify-content-center",
                )
            ],
            className="image-container-center",
        ),
    ],
    fluid=True,
    className="content-container",
)
