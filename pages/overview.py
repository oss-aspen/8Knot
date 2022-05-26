from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from .callbacks import overview_callbacks

# register the page
dash.register_page(__name__, order=2)


layout = dbc.Container(
    [
        dbc.Row([dbc.Col([html.H1(children="Overview Page - live update!")])]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id="commits-over-time"),
                        html.Label(["Date Interval"], style={"font-weight": "bold"}),
                        dcc.RadioItems(
                            id="time-interval",
                            options=[
                                {
                                    "label": "Day",
                                    "value": 86400000,
                                },  # days in milliseconds for ploty use
                                {
                                    "label": "Week",
                                    "value": 604800000,
                                },  # weeks in milliseconds for ploty use
                                {"label": "Month", "value": "M1"},
                                {"label": "Year", "value": "M12"},
                            ],
                            value="M1",
                            style={"width": "50%"},
                        ),
                    ],
                ),
                dbc.Col(
                    [
                        dcc.Graph(id="issues-over-time"),
                    ],
                ),
            ]
        ),
    ],
    fluid=True,
)