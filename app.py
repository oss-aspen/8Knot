import dash
import dash_labs as dl
import dash_bootstrap_components as dbc
import numpy as np

from db_interface.AugurInterface import AugurInterface
import os

"""
    Need to load our config parameters. 
    
    Parameters are either in the environment or they're in a config file at the same level as this file.

    Check first if we can get the parameters from the environment then default to trying to find the config
    file in the directory.
"""
try:
    assert os.environ["running_on"] == "prod"
    augur_db = AugurInterface()
except KeyError:
    augur_db = AugurInterface("./config.json")

"""
    Get our SQLAlchemy engine that connects to our database. This is declared at the global scope 
    so that it is available to all of the pages later for their queries.
"""
engine = augur_db.get_engine()


"""
    Create out Dash app with the dash_labs plugin for multi-page apps and with the Sandstone bootstrap_components theme.
"""
app = dash.Dash(
    __name__, plugins=[dl.plugins.pages], external_stylesheets=[dbc.themes.SANDSTONE]
)

"""
    Query the Augur DB for the list of all repos and orgs
    that we have available from scraping. Populate that data structure
    at the global level.
"""
print("AUGUR_ENTRY_LIST - START")

# from our list of all org/repos
pr_query = f"""SELECT * FROM augur_data.explorer_entry_list"""

df_search_bar = augur_db.run_query(pr_query)

entries = np.concatenate(
    (df_search_bar.rg_name.unique(), df_search_bar.repo_git.unique()), axis=None
)
entries = entries.tolist()
entries = sorted(entries)
entries = entries[:1000]

print(f"Num Entries: {len(entries)}")

print("AUGUR_ENTRY_LIST - END")
