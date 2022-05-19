import dash
import dash_bootstrap_components as dbc

from db_interface.AugurInterface import AugurInterface
import os

"""
    Connect to the Augur instance.

    Get all of the unique repo names and group names.

    Use those to populate the available options in the search bar.
"""

try:
    # check if we're running on production hardware. The 'running_on' variable will be set.
    os.environ['running_on'] == 'prod'
    print("Production config")
    augur_db = AugurInterface()
except KeyError:
    # otherwise, try to load the config from our local directory -- suggests we are running in local environment.
    print("Development Config")
    augur_db = AugurInterface("./config.json")

engine = augur_db.get_engine()

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.SANDSTONE])

# app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.SLATE],
#                 meta_tags=[{'name': 'viewport',
#                             'content': 'width=device-width, initial-scale=1.0'}]
#                 )

server = app.server

