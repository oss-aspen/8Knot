from dash import html, dcc
import dash
import dash_labs as dl
import dash_bootstrap_components as dbc
from .callbacks import overview_callbacks

# register the page
dl.plugins.register_page(__name__, order=2)


graph_card_1 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    id="overview-graph-title-1",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on graph 1"),
                    ],
                    id="overview-popover-1",
                    target="overview-popover-target-1",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="total_contributor_growth")],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval",
                                    html_for="contributor-growth-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="contributor-growth-time-interval",
                                        options=[
                                            {
                                                "label": "Trend",
                                                "value": -1,
                                            },
                                            {
                                                "label": "Day",
                                                "value": "D1",
                                            },
                                            {"label": "Month", "value": "M1"},
                                            {"label": "Year", "value": "M12"},
                                        ],
                                        value=-1,
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-1",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
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
                html.H4(
                    "Commits Over Time",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on overview graph 2"),
                    ],
                    id="overview-popover-2",
                    target="overview-popover-target-2",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="commits-over-time")],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="commits-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="commits-time-interval",
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
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-2",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
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

graph_card_3 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    "Issues Over Time",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on overview graph 3"),
                    ],
                    id="overview-popover-3",
                    target="overview-popover-target-3",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="issues-over-time")],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="issue-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="issue-time-interval",
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
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-3",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
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

graph_card_4 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    "Contributor Growth",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "<ACTIVE> contributors have contributed within last 6 months.\n\
                            <DRIFTING> contributors have contributed within last year but are not active.\n\
                            <AWAY> contributors haven't made any contributions in the last year at least."
                        ),
                    ],
                    id="overview-popover-4",
                    target="overview-popover-target-4",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="active_drifting_contributors")],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for="active-drifting-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id="active-drifting-interval",
                                            options=[
                                                {
                                                    "label": "Day",
                                                    "value": "D",
                                                },  # days in milliseconds for ploty use
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
                                            inline=True,
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-4",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
                                ),
                            ],
                            align="center",
                        )
                    ]
                ),
            ]
        )
    ],
    color="light",
)

layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H1(children="Overview Page - live update!")),
        ),
        dbc.Row(
            [
                dbc.Col(graph_card_1, width=6),
                dbc.Col(graph_card_4, width=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(graph_card_3, width=6),
                dbc.Col(graph_card_2, width=6),
            ]
        ),
    ],
    fluid=True,
)
