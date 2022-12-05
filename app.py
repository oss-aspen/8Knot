"""
    README -- Organization of Callback Functions

    In an effort to compartmentalize our development where possible, all callbacks directly relating
    to pages in our application are in their own files.

    For instance, this file contains the layout logic for the index page of our app-
    this page serves all other paths by providing the searchbar, page routing faculties,
    and data storage objects that the other pages in our app use.

    Having laid out the HTML-like organization of this page, we write the callbacks for this page in
    the neighbor 'app_callbacks.py' file.
"""
import pstats
import cProfile
from db_manager.AugurInterface import AugurInterface
from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import numpy as np
import sys
import os
import logging
from app_global import celery_manager, celery_app
import plotly.io as plt_io

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG)

# GLOBAL VARIABLE DECLARATIONS
engine = None
search_input = None
all_entries = None
entries = None
augur_db = None
repo_dict = None
org_dict = None


def _load_config():
    global engine
    global augur_db
    # Get config details
    augur_db = AugurInterface()
    engine = augur_db.get_engine()
    if engine is None:
        logging.critical("Could not get engine; check config or try later")
        sys.exit(1)


def _project_list_query():
    global entries
    global all_entries
    global search_input
    global augur_db
    global repo_dict
    global org_dict

    # query of available orgs / repos
    logging.debug("AUGUR_ENTRY_LIST - START")
    pr_query = f"""SELECT DISTINCT
                        r.repo_git,
                        r.repo_id,
                        r.repo_name,
                        rg.rg_name
                    FROM
                        repo r
                    JOIN repo_groups rg
                    ON rg.repo_group_id = r.repo_group_id
                    ORDER BY rg.rg_name"""

    # query for search bar entry generation
    df_search_bar = augur_db.run_query(pr_query)

    # handling case sensitive options for search bar
    entries = np.concatenate((df_search_bar.rg_name.unique(), df_search_bar.repo_git.unique()), axis=None)
    entries = entries.tolist()
    entries.sort(key=lambda item: (item, len(item)))

    # generating search bar entries
    lower_entries = [i.lower() for i in entries]
    all_entries = list(zip(lower_entries, entries))

    # generating dictionary with the git urls as the key and the repo_id and name as a list as the value pair
    repo_dict = df_search_bar[["repo_git", "repo_id", "repo_name"]].set_index("repo_git").T.to_dict("list")

    # generating dictionary with the org name as the key and the git repos of the org in a list as the value pair
    org_dict = df_search_bar.groupby("rg_name")["repo_git"].apply(list).to_dict()

    # making first selection for the search bar
    search_input = entries[0]

    logging.debug("AUGUR_ENTRY_LIST - END")


# RUN SETUP FUNCTIONS DEFINED ABOVE
_load_config()
_project_list_query()

# can import this file once we've loaded relevant global variables.
import app_callbacks

# CREATE APP OBJECT
load_figure_template(["sandstone", "minty", "slate"])

# stylesheet with the .dbc class
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

plt_io.templates["custom_dark"] = plt_io.templates["slate"]
plt_io.templates["custom_dark"]["layout"]["colorway"] = [
    "#f8dd70",
    "#c0bc5d",
    "#8e9b4c",
    "#62793d",
    "#3c582d",
    "#1c381d",
]
plt_io.templates.default = "custom_dark"

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.SLATE, dbc_css],
    suppress_callback_exceptions=True,
    background_callback_manager=celery_manager,
)

# expose the server variable so that gunicorn can use it.
server = app.server

# layout of the app stored in the app_layout file, must be imported after the app is initiated
from app_layout import layout

app.layout = layout

def main():
    # shouldn't run server in debug mode if we're in a production setting
    debug_mode = True
    try:
        if os.environ["running_on"] == "prod":
            debug_mode = False
        else:
            debug_mode = True
    except:
        debug_mode = True

    app.run(host="0.0.0.0", port=8050, debug=False, process=4, threading=False)


if __name__ == "__main__":

    try:
        if os.environ["profiling"] == "True":
            """
            Ref for how to do this:
            https://www.youtube.com/watch?v=dmnA3axZ3FY

            Credit to IDG TECHTALK
            """
            logging.debug("Profiling")

            cProfile.run("main()", "output.dat")

            with open("output_time.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("time").print_stats()

            with open("output_calls.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("calls").print_stats()
    except KeyError:
        logging.debug("---------PROFILING OFF---------")
        main()
