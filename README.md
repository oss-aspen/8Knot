# Explorer

![Pre-Commit](https://github.com/JamesKunstle/explorer/actions/workflows/pre-commit.yml/badge.svg)


Welcome to Explorer!

*tl;dr sandiego-rh/explorer organizes the visualizations and data generated in the sandiego-rh/sandiego repo as a web-app.*

The number of repositories and projects that GitHub hosts is staggering. Even more impressive is the rate at which this number is growing.
Projects on GitHub range some student projects that are likely to only be updated a handful of times ever to technological monoliths like the
Linux Kernel. Understanding the growth trajectory, contributor behavior, progress blockers, etc. intuitively is no longer feasible for individual
large projects, and is even less so for groups of projects. It is necessary that community architects and contributors alike have an accessible,
correct, and extendible resource that can aggregate and interpret the data describing these communities.

Explorer aims to be this resource, extending the work done in its sibling repo sandiego-rh/sandiego. Explorer can be thought of as a pseudo-downstream of
sandiego-rh/sandiego- visualizations of open-source community originated data are created in sandiego-rh/sandiego and are added to sandiego-rh/explorer
for more convenient user access.

The buildout of sandiego-rh/explorer is very much in its infancy but please feel free to try our app as we develop it!

## To Launch

Explorer is a plotly/Dash app that is designed to be run as a Docker container.
Scripts to build the Docker image and subsequently run the Docker container
are provided below but please make sure you have the Docker Desktop (Daemon) installed and
running on your machine.

https://docs.docker.com/get-docker/

If you have any issues with this process, please create a new issue and we'll address it!

The config.json file should be at the same level as index.

Please use the build/run scripts in the /scripts folder to handle the
construction of the Docker image and running the Docker container.

From the /explorer folder, run:

```bash
bash scripts/build_docker_image.sh
```

and then:

```bash
bash scripts/run_docker_container.sh
```
NOTE: When developing locally, each time you save reopen the chrome tab to confirm correct functionality
