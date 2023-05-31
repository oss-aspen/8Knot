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
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                children=[
                                    html.H1("Welcome to 8Knot", className="box_emissions"),
                                ]
                            )
                        )
                    ],
                    width=6,
                )
            ],
            align="center",
            justify="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            dbc.Col(
                [
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.P(
                                    """
                    8Knot goes a step beyond first-order visualizations and metrics about open source communities. Based
                    on ubiquitous Python data science and machine learning tools, the goal of this application is to make it
                    as seamless as possible to go from model to shared insights.
                    """
                                ),
                                html.P(
                                    """
                    An example usecase: Survival analysis models may be fit to the data of community behavior at the request of
                    an application user. In this paradigm, the learning and serving steps of the model are defined by the
                    application. The insights provided describe the community's behavior in an in-depth way.
                    """
                                ),
                            ]
                        )
                    )
                ],
                width=8,
            ),
            align="center",
            justify="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                children=[
                                    html.H2("Using graphs:"),
                                    html.P(
                                        """
                                        We use Plotly.js figures that are interactive and high performance.
                                        Please take a moment to try out their features to enrich your analysis possibilities.
                                        """,
                                        className="explanation-p",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li("Click and drag inside of graph to zoom."),
                                            html.Li("Double click in graph to reset scaling."),
                                            html.Li("Deselect datapoints by clicking them in sidebar."),
                                        ]
                                    ),
                                ]
                            )
                        )
                    ],
                    width=6,
                    align="start",
                ),
                dbc.Col([dcc.Graph(id="welcome_graph", figure=example_fig)], width=6),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                children=[
                                    html.H2("User Accounts:"),
                                    html.P(
                                        """
                                        If you're interested in analyzing the same groups of repos more than once,
                                        consider creating a user repo group.
                                        """
                                    ),
                                    html.P(
                                        """
                                        Assuming you've logged in, you can create user groups via the Augur frontend
                                        and then refresh your groups. You'll now be able to find groups you've created by
                                        searching for your username. For instance, if your augur username is 'USER' and the group you created is called
                                        'CUSTOM_GROUP' then you'll be find your group by searching 'USER_CUSTOM_GROUP.'
                                        """
                                    ),
                                ]
                            )
                        )
                    ],
                    width=6,
                    align="start",
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                children=[
                                    html.H2("Login Procedure"),
                                    html.Ol(
                                        [
                                            html.Li("Click 'Augur Login/Signup"),
                                            html.Li("Create or log into your account."),
                                            html.Li("'Authorize' the 8Knot application you're using."),
                                            html.Li("After redirect to 8Knot, click 'Manage Groups'"),
                                            html.Li("Create/Edit your groups by adding/removing repos."),
                                            html.Li(
                                                "Click 'Refresh Groups' in 8Knot to update application with your changes."
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        )
                    ],
                    width=6,
                    align="start",
                ),
            ],
            align="center",
            style={"marginBottom": ".5%"},
        ),
    ],
    fluid=True,
)
