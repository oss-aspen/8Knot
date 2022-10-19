# 8Knot (Explorer)

![Pre-Commit](https://github.com/JamesKunstle/explorer/actions/workflows/pre-commit.yml/badge.svg)
![Build-Push](https://github.com/JamesKunstle/explorer/actions/workflows/build-push-quay.yml/badge.svg)

Welcome to 8knot!

[Example of Application](https://eightknot.osci.io/)
---

## Introduction

8knot is a [Dash](https://dash.plotly.com/) data web-app built by Red Hat's Open Source Program Office ([OSPO](https://www.redhat.com/en/blog/channel/red-hat-open-source-program-office)).

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

8knot's contribution to further closing this gap is to provide an interface to the data collected and organized by Augur as a data web-app with both essential statistical figures,
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

[8knot](https://eightknot.osci.io/)

If you would prefer to look at our most up-to-date work, please check out the following section.

---

## Local Development

We've tried to make it as easy as possible to go from fork/clone to a running instance.

### Credentials

You will need credentials of the following form, named "env.list", at the top-level of the 8knot directory that you clone.

```
    connection_string=sqlite:///:memory:
    database=<<Database>>
    host=<<Host>>
    password=<<Your Password>>
    port=<<Port>>
    schema=augur_data
    user=<<Your Username>>
    user_type=read_only
```

To get these credentials please contact one of the maintainers of this project or ping us in our Matrix channel!

### Runtime

We use Docker containers to minimize the installation requirements for development. If you do not have Docker on your system, please follow the following guide: [Install Docker](https://docs.docker.com/engine/install/)

### Scripts

All runtime environment installation and architecture is handled in Docker containers.

Anything not handled by Docker itself (building/networking/parameterizing containers) has
been handled by the script "scripts/launch\_dev.sh". Please take a moment to become familiar with the steps in this script and suggest any improvements.

Please run the following to launch your app:

```bash
bash scripts/launch_dev.sh
```

If you encounter erroneous errors, such as if the Docker Daemon blocks connections, you'll need to run Docker
in root mode. By default we don't recommend this, but some operating systems (Ubuntu, Fedora) require this.

Please run the following if you have this problem:

```bash
sudo bash scripts/launch_dev.sh
```

If you have further problems, make sure that no current Redis instance is running on port 6379- you can
see if this is the case by running:

```bash
ps aux | grep redis
```

Kill any existing redis-server instance by ID and re-run 'launch_dev.sh'.

---

## Development Note

We use pre-commit to handle our code quality checks. Before you make a PR please make sure to install pre-commit and pass all of the checks that it requires.
