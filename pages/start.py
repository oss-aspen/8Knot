from dash import html
from app import app
import dash
from dash import dcc
from dash.dependencies import Output, Input
import plotly
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import sqlalchemy as salc
import psycopg2
import json
import numpy as np


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Start Page: User notes",
                            #className="font-weight-bold mb-4",
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
