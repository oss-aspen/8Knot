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
                        html.H1(
                            "Using 8Knot Visualizations",
                            className="main-title",
                            style={"font-size": "2.6rem !important"},
                        ),
                        html.P(
                            "Visualizations in 8Knot are created with Plotly figures. These figures come with some convenient tools that might not be immediately obvious- please take a look at a few of the options below and use them to enhance your analysis.",
                            className="body-text",
                            style={"font-size": "1.6rem !important"},
                        ),
                    ],
                    width=12,
                )
            ],
            className="mb-4",
        ),
        # Main content card with vertical sections
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        # About Graph section
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H3(
                                            "About Graph",
                                            className="section-title",
                                            style={"font-size": "1.7rem !important"},
                                        ),
                                        html.P(
                                            "Click on different parts of the graph to focus on them and zoom in for detail.",
                                            className="feature-body",
                                            style={"font-size": "1.6rem !important"},
                                        ),
                                    ],
                                    width=12,
                                )
                            ],
                            className="mb-4",
                        ),
                        # Focus Areas section
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Focus Areas",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Click on any data point to focus on specific areas of the graph for detailed analysis.",
                                                    className="feature-body",
                                                    style={"font-size": "1.6rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/focus_group.png",
                                                    className="feature-image img-fluid",
                                                    alt="Focus Areas Example",
                                                ),
                                                html.P(
                                                    "Click data points to focus on specific areas",
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
                        # Exit Focus section
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Exit Focus",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Double-click on the graph to exit focus.",
                                                    className="feature-body",
                                                    style={"font-size": "1.6rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/focus_group.png",
                                                    className="feature-image img-fluid",
                                                    alt="Exit Focus Example",
                                                ),
                                                html.P(
                                                    "Double-click to return to normal view",
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
                        # Legend Filter section
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Legend Filter",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Click on legend items to remove them from the graph; resets axes if necessary.",
                                                    className="feature-body",
                                                    style={"font-size": "1.6rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/focus_group.png",
                                                    className="feature-image img-fluid",
                                                    alt="Legend Filter Example",
                                                ),
                                                html.P(
                                                    "Click legend items to filter data",
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
                        # Plotly Toolbar section
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                html.H3(
                                                    "Plotly Toolbar",
                                                    className="section-title",
                                                    style={"font-size": "1.7rem !important"},
                                                ),
                                                html.P(
                                                    "Hover over the top right corner to see Plotly tool options. Options available: Download image, Zoom, Pan, Box Select, Lasso Select, Zoom in, Zoom out, Autoscale, and Reset Axis.",
                                                    className="feature-body",
                                                    style={"font-size": "1.6rem !important"},
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/focus_group.png",
                                                    className="feature-image img-fluid",
                                                    alt="Plotly Toolbar Example",
                                                ),
                                                html.P(
                                                    "Hover top-right corner to access Plotly tools",
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
