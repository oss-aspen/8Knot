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

## Motivations and Augur

Open Source software is everywhere, yet it is difficult to find data about Open Source projects. Project community managers, advocates, contributors, and enthusiasts ought to be able to see high-level behavioral, health, and growth trends in their repository that assist their own intuition.

Augur, a project in the [CHAOSS](https://chaoss.community/) Foundation, is closing this gap by collecting structured data about Free and Open Source Software (FOSS).

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

We would prefer any initial communication be through Matrix but if you would prefer to talk to one of our maintainers, please feel free to peruse our AUTHORS.md file where you can find contact details.

---

## Usage Examples

If you would like to see the current state of our application, we would love any user-stories or bug-reports from visiting our alpha-deployment!

[8Knot](https://eightknot.osci.io/)

If you would prefer to look at our most up-to-date work, please check out the following section.

---

## Local Development

We've tried to make it as easy as possible to go from fork/clone to a running instance.

### Credentials

You will need credentials of the following form, named "env.list", at the top-level of the 8Knot directory that you clone.
The credentials below are valid, so you can copy and use them to access a development instance of Augur.

```
    connection_string=sqlite:///:memory:
    database=astros
    host=chaoss.tv
    password=!xpk98T6?bK
    port=5432
    schema=augur_data
    user=eightknot
    user_type=read_only
```

### Runtime

We use Docker containers to minimize the installation requirements for development. If you do not have Docker on your system, please follow the following guide: [Install Docker](https://docs.docker.com/engine/install/)

In addition to singular containers we also use Docker Compose. Please make sure you have Docker Compose installed on your system. You can find documentation on doing so here: [Docker Compose](https://docs.docker.com/compose/install/)

If the following commands return sensible results then Docker and Docker Compose are installed:

```bash
docker && docker compose || docker-compose
```

(above just runs docker and docker-compose and checks if both work)

NOTE: podman-compose has been generally verified to work as well, but our preference is 'docker compose'
    podman-compose doesn't support the '--scale' flag as we would expect so we don't use it for our own
    development applications, but the application is built to work with the minimum number of containers. YMMV.

### Build and Run

8Knot is a multi-container application.

The webserver, worker-pool, and cache containers communicate with one another via docker network.

All of the build/tear-down is done with docker-compose.

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
