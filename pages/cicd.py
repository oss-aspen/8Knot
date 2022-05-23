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
        dbc.Row([dbc.Col([html.H1(children="CI/CD")])]),
    ],
    fluid=True,
)
