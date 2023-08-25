# 8Knot (Explorer)

![Pre-Commit](https://github.com/JamesKunstle/explorer/actions/workflows/pre-commit.yml/badge.svg)
![Build-Push](https://github.com/JamesKunstle/explorer/actions/workflows/build-push-quay.yml/badge.svg)

Welcome to 8Knot!

[Example of Application](https://eightknot.osci.io/)
---

## Introduction

8Knot is a [Dash](https://dash.plotly.com/) data web-app built by Red Hat's Open Source Program Office ([OSPO](https://www.redhat.com/en/blog/channel/red-hat-open-source-program-office)).

The number of repositories and projects that GitHub hosts is staggering. Even more impressive is the rate at which this number is growing.
Projects on GitHub range from student projects to technological monoliths like the
Linux Kernel. Understanding the growth trajectory, contributor behavior, progress blockers, etc. intuitively is no longer feasible for individual
large projects, and is even less so for groups of projects. It is necessary that community architects and contributors alike have an accessible,
correct, and extendable resource that can aggregate and interpret the data describing these communities.

The goal of this application is to serve Open Source community mangers, stakeholders, contributors, and enthusiasts by
providing an insightful and convenient interface to the Open Source project data set collected by the project [Augur](https://github.com/chaoss/augur) (CHAOSS).

---

## Contributing

Please see our guide to contributing to this project at the following site: [CONTRIBUTORS.md](docs/CONTRIBUTORS.md)

Once you've read that, please follow our guidance on how to add additional figures and pages to the application: [new_viz_guidance.md](/docs/new_viz_guidance.md)

---

## Application File Structure

The file-structure of our application is intuitive. Non-application files are omitted from this overview:

<pre>
8Knot
+-- pages/
    |   +-- index/
               |     +-- index_callbacks.py
               |     +-- index_layout.py
        +-- overview/
               |     +-- overview.py
               |     +-- visualizations/
                            |     +-- name_of_visualization_1.py
                            |     ...
                            |     +-- name_of_visualization_n.py
        +-- chaoss/
               |     +-- chaoss.py
               |     +-- visualizations/
                            |     +-- name_of_visualization_1.py
                            |     ...
                            |     +-- name_of_visualization_n.py
        +-- home/
               |     +-- home.py
        +-- visualization_template/
               |     +-- viz_template.py
        +-- utils/
+-- app.py
.
.
.
+-- ~other files~
</pre>


The application 'Dash' instance is defined in the 'app.py' file, as is the app.server object that our WSGI server uses, and the manager for the task-queue.

The 'Dash' application instance imports the application's base layout from the '/pages/index/index_layout.py' file. The logic to process user input to components laid out in this file (search bar, page selectors) is defined in '/pages/index/index_callbacks.py.'

Each page of the application is in its own 'pages' folder. On each page a variety of metrics and figures are rendered. These, for each page, are in the 'page_name/visualizations/' folder, and are imported into the file 'page_name.py.'

If one were to add a figure or a metric to a page, they would add it to that page's 'visualizations' folder and import the visualization into the page's respective 'page_name.py' file.

---

## Motivations and Augur

Open Source software is everywhere, yet it is difficult to find data about Open Source projects. Project community managers, advocates, contributors, and enthusiasts ought to be able to see high-level behavioral, health, and growth trends in their repository that assist their own intuition.

Augur, a project in the [CHAOSS](https://chaoss.community) Foundation, is closing this gap by collecting structured data about Free and Open Source Software (FOSS).

Quoting Augur's own README.md:

>"Augur’s main focus is to measure the overall health and sustainability of open source projects, as these types of projects are system critical for nearly every software organization or company.
>We do this by gathering data about project repositories and normalizing that into our data model to provide useful metrics about your project’s health."

8Knot's contribution to further closing this gap is to provide an interface to the data collected and organized by Augur as a data web-app with both essential statistical figures,
and higher-order machine learning and data science-informed insights.

---

## State of Development

In the insightful words of Karl Fogel from his book "Producing Open Source Software":

> "This is alpha software with known bugs. It runs, and works at least some of the time, but use at your own risk."

We are incredibly happy to have people try our application in any state, and we doubly welcome any thorough bug reports.
We would seriously recommend, however, that any conclusions drawn from this app, either realized from our deployed application or
from a local instance, be scrutinized heavily until we make a proper, stable, >1.0 release.

---

## Communication

Please feel free to join our [Matrix](https://matrix.to/#/#sandiego-rh:matrix.org) channel!

We would prefer any initial communication be through Matrix but if you would prefer to talk to one of our maintainers, please feel free to peruse our [AUTHORS.md](docs/AUTHORS.md) file where you can find contact details.

---

## Usage Examples

If you would like to see the current state of our application, we would love any user-stories or bug-reports from visiting our alpha-deployment!

[8Knot](https://eightknot.osci.io/)

If you would prefer to look at our most up-to-date work, please check out the following section.

---

## Local Development

We've tried to make it as easy as possible to go from fork/clone to a running instance.

### Credentials

You will need credentials of the following form, named `env.list`, at the top-level of the 8Knot directory that you clone.
The credentials below are valid, so you can copy and use them to access a development instance of Augur.

```
    AUGUR_DATABASE=astros
    AUGUR_HOST=chaoss.tv
    AUGUR_PASSWORD=!xpk98T6?bK
    AUGUR_PORT=5432
    AUGUR_SCHEMA=augur_data
    AUGUR_USERNAME=eightknot
    8KNOT_DEBUG=True
```

If you have a companion Augur front end application you'll need to set the following credentials in the env.list as well.
By setting these credentials, a button on the top tab of the application will become available to allow you to create an account on
your Augur front end, to log into your application via this front end, and to create user-defined groups of repos/organizations that
will become available in your application, prefixed by your Augur username (e.g. \<username\>_example_group and \<username\>_other_example).
The groups of the user who registers the 8Knot app with an Augur front end will be available to all other users- this user is considered the
application's owner.

```
    AUGUR_LOGIN_ENABLED=True
    AUGUR_APP_ID=<id>
    AUGUR_CLIENT_SECRET=<secret>
    AUGUR_SESSION_GENERATE_ENDPOINT=<endpoint>/api/unstable/user/session/generate
    AUGUR_USER_GROUPS_ENDPOINT=<endpoint>/api/unstable/user/groups/repos?columns=repo_id,repo_git
    AUGUR_USER_ACCOUNT_ENDPOINT=<endpoint>/account/settings
    AUGUR_USER_AUTH_ENDPOINT=<endpoint>/user/authorize?client_id=<AUGUR_APP_ID>response_type=code
    AUGUR_ADMIN_NAME_ENDPOINT=<endpoint>/api/unstable/application/
    AUGUR_ADMIN_GROUP_NAMES_ENDPOINT=<endpoint>/api/unstable/application/groups/names
    AUGUR_ADMIN_GROUPS_ENDPOINT=<endpoint>/api/unstable/application/group/repos
```

Note: You'll have to manually fill in the \<AUGUR_APP_ID\> in the AUGUR_USER_AUTH_ENDPOINT environment variable.

In-depth instructions for enabling 8Knot + Augur integration is available in [AUGUR_LOGIN.md](docs/AUGUR_LOGIN.md).

### Runtime

We use Docker containers to minimize the installation requirements for development. If you do not have Docker on your system, please follow the following guide: [Install Docker](https://docs.docker.com/engine/install)

In addition to singular containers we also use Docker Compose. Please make sure you have Docker Compose installed on your system. You can find documentation on doing so here: [Docker Compose](https://docs.docker.com/compose/install)

If the following commands return sensible results then Docker and Docker Compose are installed:

```bash
docker && docker compose || docker-compose
```

(above just runs docker and docker-compose and checks if both work)

NOTE: `podman-compose` has been generally verified to work as well, but our preference is `docker compose`
    `podman-compose` doesn't support the `--scale` flag as we would expect so we don't use it for our own
    development applications, but the application is built to work with the minimum number of containers. YMMV.

### Build and Run

8Knot is a multi-container application.

The app-server, worker-pool, and redis-cache containers communicate with one another via docker network.

All of the build/tear-down is done with `docker-compose`.

To start the application, run at the top-level of the 8Knot directory:

```bash
docker compose up --build
```

Due to a known deadlock, we recommend scaling-up the number of worker-pool pods deployed.
There need to be (#visualizations + 1) celery threads available for the callback_worker pool.

A concrete example: I have 6 CPU's allocated to my Docker runtime, so Celery workers will default to a concurrency of 6 processes.
However, there are 7 visualizations on the Overview page. Therefore, I will scale the 'callback_worker' pod to 2 instances,
guaranteeing that there are (2 * #CPUs = 12) available processing celery threads, ensuring that the known deadlock will be avoided.

```bash
docker compose up --build --scale query-worker=2 --scale callback-worker=2
```

To stop the application, run:

```bash
ctrl-c
```

To clean up the stopped containers, run:

```bash
docker compose down
```

---

## Development Note

We use pre-commit to handle our code quality checks. Before you make a PR please make sure to install pre-commit and pass all of the checks that it requires.
