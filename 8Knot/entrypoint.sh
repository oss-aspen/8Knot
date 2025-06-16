#!/bin/sh
# Entrypoint for app-server: chooses dev or prod mode based on GUNICORN_RELOAD env var

if [ "$DEBUG_8KNOT" = "True" ]; then
  echo "[Entrypoint] Development mode: enabling --reload and mounting source code."
  exec gunicorn --reload --bind :8080 app:server --workers 1 --threads 2 --timeout 300 --keep-alive 5
else
  echo "[Entrypoint] Production mode: running without --reload."
  exec gunicorn --bind :8080 app:server --workers 1 --threads 2 --timeout 300 --keep-alive 5
fi
