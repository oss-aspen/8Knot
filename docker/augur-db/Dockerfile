FROM postgres:16

COPY init/ /docker-entrypoint-initdb.d/

ENV POSTGRES_DB=augur
ENV POSTGRES_USER=augur
ENV POSTGRES_PASSWORD=augur
