from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

# How 8knot Works section - showing the architecture image
layout = dbc.Container(
    [
        # Centered image display
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("How 8Knot Works", className="main-title", style={"font-size": "2.6rem !important"}),
                        html.P(
                            "8Knot provides comprehensive analysis of open source project health and community dynamics using Augur's data foundation.",
                            className="body-text mb-4",
                            style={"font-size": "1.6rem !important"},
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
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
