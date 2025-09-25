from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px


def create_before_after_images(before_src, after_src, before_caption, after_caption):
    """
    Create a before/after image pair with an arrow between them.

    Args:
        before_src (str): Path to the "before" image
        after_src (str): Path to the "after" image
        before_caption (str): Caption for the before image
        after_caption (str): Caption for the after image

    Returns:
        html.Div: Container with before image, arrow, and after image
    """
    return html.Div(
        [
            # Before image
            html.Div(
                [
                    html.Img(
                        src=f"assets/{before_src}",
                        className="feature-image img-fluid",
                        alt=before_caption,
                    ),
                    html.P(
                        before_caption,
                        className="image-caption text-muted small",
                    ),
                ],
                className="before-image-container",
            ),
            # Arrow
            html.Div(
                html.Img(
                    src="assets/rightarrow.png",
                    className="arrow-image",
                    alt="Arrow pointing right",
                ),
                className="image-arrow",
            ),
            # After image
            html.Div(
                [
                    html.Img(
                        src=f"assets/{after_src}",
                        className="feature-image img-fluid",
                        alt=after_caption,
                    ),
                    html.P(
                        after_caption,
                        className="image-caption text-muted small",
                    ),
                ],
                className="after-image-container",
            ),
        ],
        className="before-after-container",
    )


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Using 8Knot Visualizations",
                            className="main-title",
                        ),
                        html.P(
                            "Visualizations in 8Knot are created with Plotly figures. These figures come with some convenient tools that might not be immediately obvious- please take a look at a few of the options below and use them to enhance your analysis.",
                            className="body-text",
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
                                        ),
                                        html.P(
                                            "Click on different parts of the graph to focus on them and zoom in for detail.",
                                            className="feature-body",
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
                                                ),
                                                html.P(
                                                    "Click on any data point to focus on specific areas of the graph for detailed analysis.",
                                                    className="feature-body",
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        create_before_after_images(
                                            "focus_area.png",
                                            "zoomed.png",
                                            "Click and drag middle of the graph to focus on specific areas",
                                            "Focused view shows detailed analysis of selected data",
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
                                                ),
                                                html.P(
                                                    "Double-click on the graph to exit focus.",
                                                    className="feature-body",
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        create_before_after_images(
                                            "zoomed.png",
                                            "zoomed_out.png",
                                            "Focused view with detailed data",
                                            "Double-click to return to normal view",
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
                                                ),
                                                html.P(
                                                    "Click on legend items to remove them from the graph; resets axes if necessary.",
                                                    className="feature-body",
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        create_before_after_images(
                                            "legend.png",
                                            "legend_sel.png",
                                            "Click on legend items to remove them from the graph",
                                            "Selected items are hidden; axes reset if necessary",
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
                                                ),
                                                html.P(
                                                    "Hover over the top right corner to see Plotly tool options. Options available: Download image, Zoom, Pan, Box Select, Lasso Select, Zoom in, Zoom out, Autoscale, and Reset Axis.",
                                                    className="feature-body",
                                                ),
                                            ],
                                            className="feature-title",
                                        ),
                                        html.Div(
                                            [
                                                html.Img(
                                                    src="assets/toolbar.png",
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
