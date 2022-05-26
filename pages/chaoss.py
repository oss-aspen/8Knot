from dash import html, dcc
import dash
import plotly.express as px
import dash_bootstrap_components as dbc
import warnings

warnings.filterwarnings("ignore")

# register the page
dash.register_page(__name__, order=3)

from .callbacks import chaoss_callbacks

layout = dbc.Container(
    [
        dbc.Row([dbc.Col([html.H1(children="Chaoss WIP Page - live update")])]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(children=[dcc.Graph(id='cont-drive-repeat')], color="#119DFF", type="dot", fullscreen=False,),
                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        "Contributions Required:",
                                        html_for="num_contributions",
                                        width={"offset": 1, "size": "auto"},
                                        style={"font-weight": "bold"},
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Input(
                                                id="num_contributions",
                                                type="number",
                                                min=1,
                                                max=15,
                                                step=1,
                                                value=4,
                                            )
                                        ],
                                        className="me-3",
                                        width=2,
                                    ),
                                    dbc.Label(
                                        "Graph View:",
                                        html_for="drive-repeat",
                                        width="auto",
                                        style={"font-weight": "bold"},
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.RadioItems(
                                                id="drive-repeat",
                                                options=[
                                                    {
                                                        "label": "Repeat",
                                                        "value": "repeat",
                                                    },
                                                    {
                                                        "label": "Drive-By",
                                                        "value": "drive",
                                                    },
                                                ],
                                                value="drive",
                                            )
                                        ],
                                        className="me-3",
                                    ),
                                ],
                                className="g-2",
                                align="center",
                                justify="start",
                            )
                        ),
                    ],
                ),
                dbc.Col(
                    [
                        dcc.Loading(children=[dcc.Graph(id='first-time-contributors')], color="#119DFF", type="dot", fullscreen=False,),
                    ],
                ),
            ]
        ),

        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(children=[dcc.Graph(id='contributors-over-time')], color="#119DFF", type="dot", fullscreen=False,),
                        #dcc.Graph(id='contributors-over-time'),

                        dbc.Form(
                            dbc.Row(
                                [
                                    dbc.Label(
                                        'Contributions Required:', 
                                        html_for='num_contribs_req', 
                                        width={"offset": 1, "size":"auto"},
                                        style={'font-weight': 'bold'}
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Input( 
                                                id='num_contribs_req', 
                                                type = 'number', 
                                                min = 1, 
                                                max= 15,
                                                step =1, 
                                                value = 4
                                            )
                                        ],
                                        className="me-3", 
                                        width= 2
                                    ),
                                    dbc.Label(
                                        'Date Interval:', 
                                        html_for='contrib-time-interval', 
                                        width="auto",
                                        style={'font-weight': 'bold'}
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.RadioItems(
                                                id='contrib-time-interval',
                                                options=[
                                                    {
                                                        'label': 'Day', 
                                                        'value': 86400000
                                                    }, #days in milliseconds for ploty use  
                                                    {
                                                        'label': 'Week', 
                                                        'value': 604800000
                                                    }, #weeks in milliseconds for ploty use
                                                    {'label': 'Month', 'value': 'M1'},
                                                    {'label': 'Year', 'value': 'M12'}
                                                ],
                                                value='M1',
                                            ),
                                        ],
                                        className="me-3",
                                    ),
                                ],
                                className="g-2",
                                align="center",
                                justify="start"
                            )
                        ),
                    ],
                ),
            ]
        )
    ], 
    fluid= True
)
