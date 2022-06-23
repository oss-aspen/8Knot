"""
    Base of app and location where required start queries are performed.
"""
import dash
import dash_labs as dl
import dash_bootstrap_components as dbc
import numpy as np
from dash_bootstrap_templates import load_figure_template

from db_interface.AugurInterface import AugurInterface
import os

# Get config details
try:
    assert os.environ["running_on"] == "prod"
    augur_db = AugurInterface()
except KeyError:
    augur_db = AugurInterface("./config.json")

engine = augur_db.get_engine()


# load styling and start app
load_figure_template(["sandstone", "minty"])

app = dash.Dash(__name__, plugins=[dl.plugins.pages], external_stylesheets=[dbc.themes.SANDSTONE])

# query of available orgs / repos
print("AUGUR_ENTRY_LIST - START")
pr_query = f"""SELECT * FROM augur_data.explorer_entry_list"""

df_search_bar = augur_db.run_query(pr_query)

entries = np.concatenate((df_search_bar.rg_name.unique(), df_search_bar.repo_git.unique()), axis=None)
entries = entries.tolist()
entries = sorted(entries)

print("AUGUR_ENTRY_LIST - END")
