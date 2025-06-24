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
import os
import sys
import logging
import dash
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
import plotly.io as plt_io
import dash_bootstrap_components as dbc
import dash_bootstrap_templates as dbt
from db_manager.augur_manager import AugurManager
import _login
from _celery import celery_app, celery_manager
import _bots as bots

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO)


"""CREATE DATABASE ACCESS OBJECT AND CACHE SEARCH OPTIONS"""
use_oauth = os.getenv("AUGUR_LOGIN_ENABLED", "False") == "True"
try:
    # create augur manager object. init fails if
    # necessary environment variables aren't available.
    augur = AugurManager(handles_oauth=use_oauth)

    # create engine. fails if test connection to DB fails.
    engine = augur.get_engine()

except KeyError:
    sys.exit(1)
except SQLAlchemyError:
    sys.exit(1)

# grab list of projects and orgs from Augur database.
augur.multiselect_startup()


"""IMPORT AFTER GLOBAL VARIABLES SET"""
import pages.index.index_callbacks as index_callbacks

# Import testing utilities for enhanced error detection in CI
if os.getenv("8KNOT_DEBUG", "False") == "True":
    import testing_utils

    testing_utils.log_service_status()


"""SET STYLING FOR APPLICATION"""
dbt.load_figure_template(["sandstone", "minty", "slate"])

# stylesheet with the .dbc class, this is a complement to the dash bootstrap templates, credit AnnMarieW
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

# making custom plotly template with custom colors on top of the slate design template
plt_io.templates["custom_dark"] = plt_io.templates["slate"]
plt_io.templates["custom_dark"]["layout"]["colorway"] = [
    "#B5B682",  # sage
    "#c0bc5d",  # citron (yellow-ish)
    "#6C8975",  # reseda green
    "#D9AE8E",  # buff (pale pink)
    "#FFBF51",  # xanthous (orange-ish)
    "#C7A5A5",  # rosy brown
]

plt_io.templates.default = "custom_dark"


"""CREATE APPLICATION"""
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.SLATE, dbc_css, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    background_callback_manager=celery_manager,
)

"""CONFIGURE FLASK-LOGIN"""
server = app.server
server = _login.configure_server_login(server)

"""REGISTER CLIENTSIDE CALLBACKS"""
# Clientside callback to handle clicking outside the search dropdown
app.clientside_callback(
    """
    function(trigger) {
        // Setup click outside behavior for search dropdown
        setTimeout(function() {
            const searchContainer = document.getElementById('search-input-container');
            const dropdown = document.getElementById('search-dropdown-popup');
            const input = document.getElementById('my-input');
            
            if (!searchContainer || !dropdown || !input) {
                return;
            }
            
            // Function to handle clicks outside
            function handleClickOutside(event) {
                // Check if click is outside both the search container and dropdown
                if (!searchContainer.contains(event.target) && !dropdown.contains(event.target)) {
                    // Hide dropdown when clicking outside
                    dropdown.style.display = 'none';
                }
            }
            
            // Function to show dropdown when input gets focus
            function handleInputFocus() {
                dropdown.style.display = 'block';
            }
            
            // Remove existing listeners to avoid duplicates
            document.removeEventListener('click', handleClickOutside);
            input.removeEventListener('focus', handleInputFocus);
            
            // Add the event listeners
            document.addEventListener('click', handleClickOutside);
            input.addEventListener('focus', handleInputFocus);
            
        }, 100);
        
        return window.dash_clientside.no_update;
    }
    """,
    dash.dependencies.Output('search-dropdown-popup', 'data-click-outside-initialized', allow_duplicate=True),
    dash.dependencies.Input('cache-init-trigger', 'children'),
    prevent_initial_call='initial_duplicate'
)

"""HEALTH CHECK ENDPOINT"""
#HELLO????

@server.route("/health")
def health_check():
    """Simple health check endpoint for CI/CD testing"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        return {"status": "healthy", "database": "connected", "timestamp": str(pd.Timestamp.now())}, 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": str(pd.Timestamp.now())}, 500


"""DASH PAGES LAYOUT"""
# layout of the app stored in the app_layout file, must be imported after the app is initiated
from pages.index.index_layout import layout

app.layout = layout

"""DASH STARTUP PARAMETERS"""

if os.getenv("8KNOT_DEBUG", "False") == "True":
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_hot_reload=True)

"""GITHUB BOTS LIST"""
bots_list = bots.get_bots_list()
