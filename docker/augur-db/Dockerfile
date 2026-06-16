# Pre-populated Augur DB image, published as ghcr.io/oss-aspen/8knot-min-db.
# Build requires the data dump at init/03_data.sql (gitignored, maintainer-supplied).
# See README.md for the build-and-push workflow.
FROM postgres:16

COPY init/ /docker-entrypoint-initdb.d/

ENV POSTGRES_DB=augur
ENV POSTGRES_USER=augur
ENV POSTGRES_PASSWORD=augur
