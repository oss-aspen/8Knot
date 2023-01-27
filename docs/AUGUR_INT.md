# **8Knot+Augur Integration**

## **Intro**
---

A user should be able to:
1. Create a group of repos and orgs that they want to see aggregate for and
2. Access that group in 8Knot.

## **Preparation**
---
1. Clone [github.com/oss-aspen/8Knot/augur_int]
   - We use a docker compose multi-container application build strategy.
   - Ports 8050 (*Dash*) and 6379 (*Redis*) are assumed to be available. If this isn't possible, modifications to the docker-compose.yml file may be necessary.
   - Inter-pod name resolution is done with Docker network's DNS.

2. Create an application in Augur front-end
   - Create an account at chaoss.tv:5038.
   - Create an application in your account to get an *app_id* and a *client_secret* needed for your local 8Knot instance. You can use the url [http://0.0.0.0:8050/] if you're developing locally.

3. Prepare client environment
   - App will communicate w/ Augur front-end via HTTP and w/ its database Augur instance via direct connection.
     - The following environment variables will need to be available to the application at startup in an 'env.list' file at the same directory-level at 'app.py':
       - AUGUR_DATABASE=
       - AUGUR_HOST=
       - AUGUR_PASSWORD=
       - AUGUR_PORT=
       - AUGUR_SCHEMA=
       - AUGUR_USERNAME=
       - AUGUR_APP_ID=
         - You'll need to use the *app_id* from the Augur front-end here.
       - AUGUR_CLIENT_SECRET=
         - You'll need to use the *client_secret* from the Augur front-end here.
       - AUGUR_SESSION_GENERATE_ENDPOINT=http://chaoss.tv:5038/api/unstable/user/session/generate
       - AUGUR_USER_GROUPS_ENDPOINT=http://chaoss.tv:5038/api/unstable/user/groups/repos?columns=repo_id,repo_git
       - AUGUR_USER_ACCOUNT_ENDPOINT=http://chaoss.tv:5038/account/settings
       - AUGUR_USER_AUTH_ENDPOINT=http://chaoss.tv:5038/user/authorize?client_id=<AUGUR_APP_ID>&response_type=code
         - You'll need to use the *app_id* from the Augur front-end here to fill in the "<AUGUR_APP_ID>".
       - 8KNOT_DEBUG=True

    - ^^ above credentials file will be shared w/ Mizzou group for FOSDEM.

## **Running Application**
---
1. You can build the application inside of the '8Knot' directory with the command:
```
docker compose up --build
```
2. The application is stopped by:
```
ctrl-c
```

## **8Knot at Runtime**
---
- Log into Augur with 'Login' button in the top right of the page.

- You should be redirected to the Augur front-end that you specified in the 'env.list' file, be able to create or log into your profile, and be redirected back to the index (home) page of 8Knot.

- When you've been redirected, your Augur username should be filled-in where the 'Login' button was originally. (Log-out not currently supported. Will need to inspect page and delete Application/Local Storage and Application/Session Storage cache and refresh page to 'log out' of 8Knot.)

- If there's a problem logging in, you should still see the login button but a popover should tell you that login has failed. Detailed logs of failure are in the running terminal.

- Augur front-end defined groups are available in the searchbar pre-fixed with your username.
