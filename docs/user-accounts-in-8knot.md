# How do user accounts work in 8Knot (OAuth and session handling)

8Knot has user accounts- there are log in / log out buttons, and user groups are persist across logins.
However, 8Knot doesn't directly handle these accounts. Instead, Augur manages the user's accounts and 8Knot connects as an OAuth client.

This document describes how this flow works, what parts of the codebase are relevant, and where there are currently (4/22/24) gaps in the implementation.

## Notes
- `access_token` and `bearer_token` are the same thing

## How the flow works

Let's assume that we've got a functional 8Knot instance running that's been configured as an oauth client for Augur. We've documented how to connect an application to the Augur frontend as an oauth client (specifically, you can find it on the 8Knot welcome page) but let's dig deeper into how this works on the application server.

Assume:
1. Your application is configured with a valid `application_id` and `client_secret`. e.g. login, refresh, and manage groups all work as expected.

Then the following happens when the user clicks `Augur Log in / Sign up` in the UI:
1. The frontend application href's to `http://<host>/login/`.
2. `/login/` is a Flask route that the backend serves. It's defined in the file `8Knot/8Knot/_login.py`.
3. The backend route gets the OAuth provider route from the environment (`OAUTH_AUTHORIZE_URL`) and redirects to that host with the URL format: `http://<OAUTH_AUTHORIZE_URL>/?client_id=<id>&response_type=code/`.
4. The user should be routed to the Augur frontend where they can log in and authorize 8Knot to use their account.
5. When the user authorizes 8Knot's use of their account, Augur will redirect them back to the registered 8Knot application route `http://<host>/authorize/?code=<temp_auth_code>`.
6. The 8Knot backend `/authorize/` route receives this code as a query parameter in the URL and uses it, along with the application's client secret, to post a request to the `OAUTH_TOKEN_URL` intending to receive a `bearer token` and `refresh token` from the Augur frontend.
7. The Augur frontend, if all values are acceptable, returns a `bearer token`, a `refresh token`, a `token expiration` and a `username`.
8. 8Knot creates a random `id_number = str(uuid.uuid1())` for the user and stores a JSON payload `{username, access_token, refresh_token, expiration}` in Redis under that UUID.
9. Finally, `login_user(User(id_number))` is called, setting an HTTP-only `session` cookie in the client's browser that will be used by FlaskLogin to handle the user's session in the future.

## Topics out of scope for this document:

- oauth2.0 flow implementation details: [an overview](https://www.digitalocean.com/community/tutorials/an-introduction-to-oauth-2)
- Flask Login: [docs](https://flask-login.readthedocs.io/en/latest/#flask_login.login_user)

## Current implementation gaps:

1. The use of the user's `access_token` is zero-shot. If authentication fails, it fails silently without notifying the user that they should log in again.
2. We don't currently user the refresh token even though it's available.
3. Session cookies are `HTTP-only` but not `Secure` (require TLS) in general, but this should only be the case in development.
