from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

layout = dbc.Container(
    [
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
                            className="border-0 bg-transparent",
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
