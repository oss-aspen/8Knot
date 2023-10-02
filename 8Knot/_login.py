import os
from flask_login import (
    current_user,
    LoginManager,
    logout_user,
    login_user,
    UserMixin,
)
import redis
from flask import url_for, redirect, abort, session, request, flash, current_app
import logging
import json
import secrets
import uuid
from urllib.parse import urlencode
import requests
import json


def configure_server_login(server):
    """
        Configures Dash (Flask) server- makes login routes available.
    Args:
        server (Flask.server): Flask application server

    Returns:
        Flask.server: Server configured w/ Flask-Login
    """

    # sets a parameter that's used for cryptographic session cookie signing.
    server.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

    # writes OAuth parameters to the app config.
    server.config["OAUTH2_PROVIDERS"] = {
        os.environ.get("OAUTH_CLIENT_NAME"): {
            "client_id": os.environ.get("OAUTH_CLIENT_ID"),
            "client_secret": os.environ.get("OAUTH_CLIENT_SECRET"),
            "authorize_url": os.environ.get("OAUTH_AUTHORIZE_URL"),
            "token_url": os.environ.get("OAUTH_TOKEN_URL"),
            "redirect_uri": os.environ.get("OAUTH_REDIRECT_URI"),
        }
    }

    # create flask-login object
    login = LoginManager(server)
    login.login_view = "/"

    class User(UserMixin):
        """
        Basic user class expected by Flask-Login
        flow.
        """

        def __init__(self, id):
            self.id = id

    @login.user_loader
    def load_user(id):
        """
            Loads user from session into User object
            if the user's session exists.

        Args:
            id (int): ID from session cookie to lookup user in user sessions.

        Returns:
            User | None: User object if user ID in session, None otherwise.
        """
        users_cache = redis.StrictRedis(
            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", ""),
        )
        try:
            users_cache.ping()
        except redis.exceptions.ConnectionError:
            logging.error("LOAD_USER: Could not connect to users-cache.")
            return None

        # return the JSON of a user that was set in the Redis instance
        if users_cache.exists(id):
            usn = json.loads(users_cache.get(id))["username"]
            return User(id)
        return None

    @server.route("/logout/")
    def logout():
        """
            If the user is signed in, removes the user
            from the user sessions cache and logs the user
            out via Flask-Login flow.

        Args:
            None
        Returns:
            None

        """
        users_cache = redis.StrictRedis(
            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", ""),
        )
        try:
            users_cache.ping()
        except redis.exceptions.ConnectionError:
            logging.error("LOGOUT: Could not connect to users-cache.")
            return redirect("/")

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
        """
            Redirects the user's browser to the registered
            OAuth provider Authorization site.

        Args:
            None
        Returns:
            None
        """
        users_cache = redis.StrictRedis(
            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", ""),
        )
        try:
            users_cache.ping()
        except redis.exceptions.ConnectionError:
            logging.error("LOGIN: Could not connect to users-cache.")
            return redirect("/")

        provider = os.environ.get("OAUTH_CLIENT_NAME")

        if not current_user.is_anonymous:
            return redirect("/")

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
        """
            Target of redirection from OAuth provider authorization server.
            Performs OAuth flow to get access_token and refresh_token.

        Args:
            None
        Returns:
            None
        """
        users_cache = redis.StrictRedis(
            host=os.getenv("REDIS_SERVICE_USERS_HOST", "redis-users"),
            port=6379,
            password=os.getenv("REDIS_PASSWORD", ""),
        )
        try:
            users_cache.ping()
        except redis.exceptions.ConnectionError:
            logging.error("AUTHORIZE: Could not connect to users-cache.")
            return redirect("/")

        provider = os.environ.get("OAUTH_CLIENT_NAME")

        if not current_user.is_anonymous:
            return redirect("/")

        provider_data = current_app.config["OAUTH2_PROVIDERS"].get(provider)
        if provider_data is None:
            abort(404)

        # if there was an authentication error, flash the error messages and exit
        if "error" in request.args:
            for k, v in request.args.items():
                if k.startswith("error"):
                    flash(f"{k}: {v}")
            return redirect("/")

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

    return server
