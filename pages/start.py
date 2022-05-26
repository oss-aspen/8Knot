from dash import html
import dash
import dash_bootstrap_components as dbc
import dash

# register the page
dash.register_page(__name__, path='/', order=1)

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.P(
                            "Start page text holder.",
                            className="text-center font-weight-bold mb-4",
                        )
                    ]
                )
            ]
        ),
    ],
    fluid=True,
)
