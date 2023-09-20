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
import secrets
import uuid
from urllib.parse import urlencode
import requests
import json
import dash
from redis import StrictRedis
from sqlalchemy.exc import SQLAlchemyError
import plotly.io as plt_io
from celery import Celery
from dash import CeleryManager, Input, Output
import dash_bootstrap_components as dbc
from flask import url_for, redirect, abort, session, request, flash, current_app
from flask_login import (
    current_user,
    LoginManager,
    logout_user,
    login_user,
    UserMixin,
    login_required,
)
from dash_bootstrap_templates import load_figure_template
from db_manager.augur_manager import AugurManager
import worker_settings

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO
)

"""CREATE CELERY TASK QUEUE AND MANAGER"""
celery_app = Celery(
    __name__,
    broker=worker_settings.REDIS_URL,
    backend=worker_settings.REDIS_URL,
)

celery_app.conf.update(
    task_time_limit=84600, task_acks_late=True, task_track_started=True
)

celery_manager = CeleryManager(celery_app=celery_app)


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


"""SET STYLING FOR APPLICATION"""
load_figure_template(["sandstone", "minty", "slate"])

# stylesheet with the .dbc class, this is a complement to the dash bootstrap templates, credit AnnMarieW
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

# making custom plotly template with custom colors on top of the slate design template
plt_io.templates["custom_dark"] = plt_io.templates["slate"]
plt_io.templates["custom_dark"]["layout"]["colorway"] = [
    "#B5B682",  # sage
    "#c0bc5d",  # olive green
    "#6C8975",  # xanadu
    "#485B4E",  # feldgrau (dark green)
    "#3c582d",  # hunter green
    "#376D39",
]  # dartmouth green
plt_io.templates.default = "custom_dark"


"""CREATE APPLICATION"""
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.SLATE, dbc_css, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    background_callback_manager=celery_manager,
)

"""CONFIGURE FLASK-LOGIN STUFF"""
server = app.server
server.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
server.config["OAUTH2_PROVIDERS"] = {
    os.environ.get("OAUTH_CLIENT_NAME"): {
        "client_id": os.environ.get("OAUTH_CLIENT_ID"),
        "client_secret": os.environ.get("OAUTH_CLIENT_SECRET"),
        "authorize_url": os.environ.get("OAUTH_AUTHORIZE_URL"),
        "token_url": os.environ.get("OAUTH_TOKEN_URL"),
        "redirect_uri": os.environ.get("OAUTH_REDIRECT_URI"),
    }
}

# CREATE FLASK-LOGIN OBJECT
login = LoginManager(server)
login.login_view = "index"


"""DASH PAGES LAYOUT"""
# layout of the app stored in the app_layout file, must be imported after the app is initiated
from pages.index.index_layout import layout

app.layout = layout

"""CLIENTSIDE CALLBACK FOR LOGOUT + REFRESH"""
# I know what you're thinking- "This callback shouldn't be here!"
# well, circular imports are a hassle, and the 'app' object from this
# file can't be imported into index_callbacks.py file where it should be.
# This callback handles logging a user out of their preferences.
# app.clientside_callback(
#     """
#     function(logout, refresh) {

#         // gets the string representing the component_id and component_prop that triggered the callback.
#         const triggered = window.dash_clientside.callback_context.triggered.map(t => t.prop_id)[0]
#         console.log(triggered)

#         if(triggered == "logout-button.n_clicks"){
#             // clear user's localStorage,
#             // pattern-match key's suffix.
#             const keys = Object.keys(localStorage)
#             for (let key of keys) {
#                 if (String(key).includes('_dash_persistence')) {
#                     localStorage.removeItem(key)
#                 }
#             }

#             // clear user's sessionStorage,
#             // pattern-match key's suffix.
#             const sesh = Object.keys(sessionStorage)
#             for (let key of sesh) {
#                 if (String(key).includes('_dash_persistence')) {
#                     sessionStorage.removeItem(key)
#                 }
#             }
#         }
#         else{
#             // trigger user preferences redownload
#             sessionStorage["is-client-startup"] = true
#         }

#         // reload the page,
#         // redirect to index.
#         window.location.reload()
#         return "/"
#     }
#     """,
#     Output("url", "pathname"),
#     Input("logout-button", "n_clicks"),
#     prevent_initial_call=True,
# )


"""FLASK-LOGIN ROUTES + UTILITIES"""


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login.user_loader
def load_user(id):
    users_cache = StrictRedis(
        host="redis-users",
        port=6379,
        password=os.getenv("REDIS_PASSWORD", ""),
    )

    # return the JSON of a user that was set in the Redis instance
    if users_cache.exists(id):
        usn = json.loads(users_cache.get(id))["username"]
        return User(id)
    return None


@server.route("/logout/")
def logout():
    users_cache = StrictRedis(
        host="redis-users",
        port=6379,
        password=os.getenv("REDIS_PASSWORD", ""),
    )

    if current_user.is_authenticated:
        c_id = current_user.get_id()
        users_cache.delete(c_id)
        logout_user()
        logging.warning(f"USER {c_id} LOGGED OUT")
    else:
        logging.warning("TRIED TO LOG OUT")
    return redirect("/")


@server.route("/login/")
def oauth2_authorize():
    users_cache = StrictRedis(
        host="redis-users",
        port=6379,
        password=os.getenv("REDIS_PASSWORD", ""),
    )

    provider = os.environ.get("OAUTH_CLIENT_NAME")

    if not current_user.is_anonymous:
        return redirect(url_for("index"))

    provider_data = current_app.config["OAUTH2_PROVIDERS"].get(provider)
    if provider_data is None:
        abort(404)

    # generate a random string for the state parameter
    session["oauth2_state"] = secrets.token_urlsafe(16)

    # create a query string with all the OAuth2 parameters
    qs = urlencode(
        {
            "client_id": provider_data["client_id"],
            # "redirect_uri": url_for("oauth2_callback", _external=True),
            "response_type": "code",
            # "state": session["oauth2_state"],
        }
    )

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(provider_data["authorize_url"] + "?" + qs)


@server.route("/authorize/")
def oauth2_callback():
    users_cache = StrictRedis(
        host="redis-users",
        port=6379,
        password=os.getenv("REDIS_PASSWORD", ""),
    )

    provider = os.environ.get("OAUTH_CLIENT_NAME")

    if not current_user.is_anonymous:
        return redirect(url_for("index"))

    provider_data = current_app.config["OAUTH2_PROVIDERS"].get(provider)
    if provider_data is None:
        abort(404)

    # if there was an authentication error, flash the error messages and exit
    if "error" in request.args:
        for k, v in request.args.items():
            if k.startswith("error"):
                flash(f"{k}: {v}")
        return redirect(url_for("index"))

    # make sure that the state parameter matches the one we created in the
    # authorization request
    # if request.args["state"] != session.get("oauth2_state"):
    #     abort(401)

    # make sure that the authorization code is present
    if "code" not in request.args:
        abort(401)

    # exchange the authorization code for an access token
    response = requests.post(
        provider_data["token_url"],
        data={
            "client_id": provider_data["client_id"],
            "client_secret": provider_data["client_secret"],
            "code": request.args["code"],
            "grant_type": "code",
            "redirect_uri": url_for("oauth2_callback", _external=True),
        },
        headers={
            "Accept": "application/json",
            "Authorization": f"Client {provider_data['client_secret']}",
        },
    )
    logging.warning("Received response from authorize endpoint")

    # check whether login worked
    if response.status_code != 200:
        abort(401)

    # if login worked, get the token
    resp = response.json()
    oauth2_token = resp.get("access_token")
    if not oauth2_token:
        abort(401)
    logging.debug("Got token from authorize endpoint")

    # get remaining credentials
    username = resp.get("username")
    oauth2_refresh = resp.get("refresh_token")
    oauth2_token_expires = resp.get("expires")

    # random ID used to identify user.
    id_number = str(uuid.uuid1())

    logging.warning("Creating new user")
    serverside_user_data = {
        "username": username,
        "access_token": oauth2_token,
        "refresh_token": oauth2_refresh,
        "expiration": oauth2_token_expires,
    }
    users_cache.set(id_number, json.dumps(serverside_user_data))

    login_user(User(id_number))
    logging.warning("User logged in")

    # forward-slash redirect because dash's index route has another name
    return redirect("/")


"""DASH STARTUP PARAMETERS"""

if os.getenv("8KNOT_DEBUG", "False") == "True":
    app.enable_dev_tools(dev_tools_ui=True, dev_tools_hot_reload=False)

if __name__ == "__main__":
    print(
        "We've deprecated the Flask/Dash debug webserver.\
         Please use gunicorn to run application or docker/podman compose."
    )
