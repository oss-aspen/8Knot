from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

# register the page
dash.register_page(__name__, path="/welcome", order=5)

# This is just a stand-in until we wire up a more interesting visualization.
example_fig = px.scatter(
    x=[1, 2, 3, 4, 5, 6],
    y=[1, 2, 3, 4, 5, 6],
    color=["blue", "red", "green", "yellow", "purple", "brown"],
    labels={"x": "X Values", "y": "Y Values"},
    size_max=19,
    size=[1, 1, 1, 1, 1, 1],
)

example_fig.update_layout(
    title={
        "text": "Example Figure",
        "y": 0.9,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
    }
)

layout = dbc.Container(
    className="welcome_container",
    children=[
        html.Div(
            className="welcome_message welcome_section",
            children=[
                # html.H1("Welcome to 8Knot"),
                html.Img(src="assets/logo-color.png"),
                html.P(
                    """
                    Open source communities are difficult to understand. 8Knot serves community stakeholders by
                    providing a platform to host advanced analysis of community behavior through higher-order metrics and visualizations.
                    """
                ),
            ],
        ),
        html.Div(
            className="welcome_content_section shadow",
            children=[
                html.Div(
                    className="welcome_section_header",
                    children=[html.P("Pages Available")],
                ),
                html.Div(
                    className="welcome_section_content",
                    children=[
                        html.Div(
                            className="pages_overview_container shadow",
                            children=[
                                html.H2("Overview"),
                                html.P(
                                    """
                                    Track large community trends over time based on common contributions.
                                   """
                                ),
                            ],
                        ),
                        html.Div(
                            className="pages_overview_container shadow",
                            children=[
                                html.H2("Chaoss"),
                                html.P("Advanced metrics defined and refined by the CHAOSS foundation."),
                            ],
                        ),
                        html.Div(
                            className="pages_overview_container shadow",
                            children=[
                                html.H2("Company"),
                                html.P(
                                    "Summarizing likely company and institution affiliation with contributor behavior."
                                ),
                            ],
                        ),
                        html.Div(
                            className="pages_overview_container shadow",
                            children=[
                                html.H2("Info"),
                                html.P("Information about visualizations and definitions of any terms used."),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="welcome_content_section shadow",
            children=[
                html.Div(
                    className="welcome_section_content welcome_section_instructions",
                    children=[
                        html.Div(
                            className="instruction_header",
                            children=[html.P("Highlighted Plotly.js features for enriched analysis")],
                        ),
                        html.Div(
                            className="instruction_container",
                            children=[
                                html.Div(
                                    className="instruction_item shadow",
                                    children=[
                                        html.H3("1"),
                                        html.P(
                                            "Click and drag inside of the graph to focus/zoom on a subset of the data."
                                        ),
                                        html.Div(
                                            className="instruction_item_images",
                                            children=[
                                                html.Img(src="assets/click-zoom-graph.png"),
                                                html.Img(className="arrow_icon", src="assets/rightarrow.png"),
                                                html.Img(src="assets/zoomed-graph.png"),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_item shadow",
                                    children=[
                                        html.H3("2"),
                                        html.P("Double-click on the graph to exit focus."),
                                        html.Div(
                                            className="instruction_item_images",
                                            children=[
                                                html.Img(src="assets/zoomed-graph.png"),
                                                html.Img(className="arrow_icon", src="assets/rightarrow.png"),
                                                html.Img(src="assets/normal-graph.png"),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_item shadow",
                                    children=[
                                        html.H3("3"),
                                        html.P(
                                            "Click on legend items to remove them from the graph; resets axes if necessary."
                                        ),
                                        html.Div(
                                            className="instruction_item_images",
                                            children=[
                                                html.Img(src="assets/all-categories-graph.png"),
                                                html.Img(className="arrow_icon", src="assets/rightarrow.png"),
                                                html.Img(src="assets/no-stale-graph.png"),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ],
)
