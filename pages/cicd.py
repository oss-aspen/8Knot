from dash import html, dcc
import dash
import dash_labs as dl
import dash_bootstrap_components as dbc

# register the page
dl.plugins.register_page(__name__, order=4)

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col([html.H1(children="CICD Temp Page!")]),
            ]
        ),
    ],
    fluid=True,
)
