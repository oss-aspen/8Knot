"""
    Base of app and location where required start queries are performed.
"""
import dash
import dash_labs as dl
import dash_bootstrap_components as dbc
import numpy as np
from dash_bootstrap_templates import load_figure_template
import logging

from db_interface.AugurInterface import AugurInterface
import os
import sys

logging.basicConfig(level=logging.DEBUG)

# Get config details
try:
    assert os.environ["running_on"] == "prod"
    augur_db = AugurInterface()
except KeyError:
    # check that config file is available
    if os.path.exists("config.json"):
        augur_db = AugurInterface("./config.json")
    else:
        print("No 'config.json' available at top level. Config required by name.")
        sys.exit(1)

engine = augur_db.get_engine()
if engine is None:
    print("Could not get engine; check config or try later")
    sys.exit(1)


# load styling and start app
load_figure_template(["sandstone", "minty"])

app = dash.Dash(__name__, plugins=[dl.plugins.pages], external_stylesheets=[dbc.themes.SANDSTONE])

# query of available orgs / repos
logging.debug("AUGUR_ENTRY_LIST - START")
pr_query = f"""SELECT * FROM augur_data.explorer_entry_list"""

df_search_bar = augur_db.run_query(pr_query)

entries = np.concatenate((df_search_bar.rg_name.unique(), df_search_bar.repo_git.unique()), axis=None)
entries = entries.tolist()
entries.sort(key=lambda item: (item, len(item)))
search_input = entries[0]

logging.debug("AUGUR_ENTRY_LIST - END")
