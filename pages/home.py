from dash import html
import dash
import dash_bootstrap_components as dbc

# register the page
dash.register_page(__name__, path="/", order=1)

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Start Page: User notes",
                            # className="font-weight-bold mb-4",
                        ),
                        html.P(
                            "This is WIP and format changes to come. Visualization are on other pages",
                            className="font-weight-bold mb-4",
                        ),
                        html.P(
                            "Plotly graphs have a mode bar if you hover over the top of the title.",
                            className="font-weight-bold mb-4",
                        ),
                        html.P(
                            "If you want to reset the view of a graph with customization options, toggle one of the options to reset the view.",
                            className="font-weight-bold mb-4",
                        ),
                    ]
                )
            ]
        ),
    ],
    fluid=True,
)
