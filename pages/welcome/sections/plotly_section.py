from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

layout = html.Div(
    className="tab_section_container",
    children=[
        html.Div(
            className="card_section_container",
            children=[
                html.Div(
                    className="card_section_container_centered",
                    children=[
                        html.Div(
                            className="card_section_description",
                            children=[
                                html.H1("Using Plotly Figures"),
                                html.P(
                                    """
                            Visualizations in 8Knot are created with Plotly figures. These figures come with
                            some convenient tools that might not be immediately obvious- please take a look at a few of
                            the options below and use them to enhance your analysis.
                            """
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="card_section_body card_section_body_vertical",
                    children=[
                        html.Div(
                            className="instruction_card",
                            children=[
                                html.H2("1. Focus Area"),
                                html.P(
                                    """
                                    Click and drag inside of the graph to focus/zoom on a subset of the data.
                                   """
                                ),
                                html.Div(
                                    className="plotly_instructions_section",
                                    children=[
                                        html.Img(
                                            className="plotly_instructions_section_img",
                                            src="assets/welcome_plotly_section/click-zoom-graph.png",
                                        ),
                                        html.Img(
                                            className="arrow_icon",
                                            src="assets/welcome_plotly_section/rightarrow.png",
                                        ),
                                        html.Img(
                                            className="plotly_instructions_section_img",
                                            src="assets/welcome_plotly_section/zoomed-graph.png",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="instruction_card",
                            children=[
                                html.H2("2. Exit Focus"),
                                html.P("Double-click on the graph to exit focus."),
                                html.Div(
                                    className="plotly_instructions_section",
                                    children=[
                                        html.Img(
                                            className="plotly_instructions_section_img",
                                            src="assets/welcome_plotly_section/zoomed-graph.png",
                                        ),
                                        html.Img(
                                            className="arrow_icon",
                                            src="assets/welcome_plotly_section/rightarrow.png",
                                        ),
                                        html.Img(
                                            className="plotly_instructions_section_img",
                                            src="assets/welcome_plotly_section/normal-graph.png",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="instruction_card",
                            children=[
                                html.H2("3. Legend Filter"),
                                html.P(
                                    "Click on legend items to remove them from the graph; resets axes if necessary."
                                ),
                                html.Div(
                                    className="plotly_instructions_section",
                                    children=[
                                        html.Img(
                                            className="plotly_instructions_section_img",
                                            src="assets/welcome_plotly_section/all-categories-graph.png",
                                        ),
                                        html.Img(
                                            className="arrow_icon",
                                            src="assets/welcome_plotly_section/rightarrow.png",
                                        ),
                                        html.Img(
                                            className="plotly_instructions_section_img",
                                            src="assets/welcome_plotly_section/no-stale-graph.png",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
