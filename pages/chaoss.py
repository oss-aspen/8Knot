from dash import html, dcc
import dash
import dash_labs as dl
import plotly.express as px
import dash_bootstrap_components as dbc
import warnings

warnings.filterwarnings("ignore")

# register the page
dl.plugins.register_page(__name__, order=3)

from .callbacks import chaoss_callbacks

graph_card_1 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(id = "chaoss-graph-title-1", className="card-title", style={"text-align": "center"}),
                
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "Information on graph 1"),
                    ],
                    id="chaoss-popover-1",
                    target="chaoss-popover-target-1",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(children=[dcc.Graph(id='cont-drive-repeat')], color="#119DFF", type="dot", fullscreen=False,),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Graph View:",
                                    html_for="drive-repeat",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
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
                                            inline=True,
                                        ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button("About Graph", id="chaoss-popover-target-1", color="secondary",size="sm"),
                                    width= "auto",
                                    style={"padding-top": ".5em"}
                                )
                            ],
                            align = "center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Contributions Required:",
                                    html_for="num_contributions",
                                    width={ "size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                        dbc.Input(
                                            id="num_contributions",
                                            type="number",
                                            min=1,
                                            max=15,
                                            step=1,
                                            value=4,
                                        ),    
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
    color="light",
)

graph_card_2 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("First Time Contributions Per Quarter", className="card-title", style={"text-align": "center"}),
                
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "Information on graph 2"),
                    ],
                    id="chaoss-popover-2",
                    target="chaoss-popover-target-2",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
    
                dcc.Loading(children=[dcc.Graph(id='first-time-contributions')], color="#119DFF", type="dot", fullscreen=False,),
                dbc.Row(
                    dbc.Button("About Graph", id="chaoss-popover-target-2", color="secondary",size= "small"),
                    style={"padding-top": ".5em"}
                ),
            ]
        ),
    ],
    color="light",
)

graph_card_3 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4("Contributor Types Over Time", className="card-title", style={"text-align": "center"}),
                
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "Information on graph 3"),
                    ],
                    id="chaoss-popover-3",
                    target="chaoss-popover-target-3",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(children=[dcc.Graph(id='contributors-over-time')], color="#119DFF", type="dot", fullscreen=False,),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    'Date Interval:',
                                    html_for='contrib-time-interval',
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                        dbc.RadioItems(
                                            id='contrib-time-interval',
                                            options=[
                                                {
                                                    'label': 'Day', 
                                                    'value': 86400000
                                                }, #days in milliseconds for ploty use  
                                                {
                                                    "label": "Week",
                                                    "value": 604800000
                                                },#weeks in milliseconds for ploty use
                                                {'label': 'Month', 'value': 'M1'},
                                                {'label': 'Year', 'value': 'M12'}
                                            ],
                                            value="M1",
                                            inline=True,
                                        ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button("About Graph", id="chaoss-popover-target-3", color="secondary",size="sm"),
                                    width= "auto",
                                    style={"padding-top": ".5em"}
                                )
                            ],
                            align = "center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Contributions Required:",
                                    html_for='num_contribs_req',
                                    width={ "size": "auto"},
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                        dbc.Input(
                                            id='num_contribs_req',
                                            type="number",
                                            min=1,
                                            max=15,
                                            step=1,
                                            value=4,
                                        ),    
                                    className="me-2",
                                    width=2,
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
    color="light",
)


layout = dbc.Container(
    [
        dbc.Row([dbc.Col([html.H1(children="Chaoss WIP Page - live update")])]),
        dbc.Row(
            [
                dbc.Col(graph_card_1, width=6),
                dbc.Col(graph_card_2, width=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(graph_card_3, width = 6),
            ]
        ),
    ],
    fluid=True,
)
