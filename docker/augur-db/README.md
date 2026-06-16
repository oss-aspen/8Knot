# min_db — pre-populated local Augur database

A ready-to-use PostgreSQL image with real Augur data baked in, so you can run
8Knot or notebooks locally without access to a remote Augur instance. It is the
populated counterpart to `ghcr.io/chaoss/augur_empty_database`.

Published image: `ghcr.io/oss-aspen/8knot-min-db:latest` (public).

## For users

1. In your `.env`, point 8Knot at the local DB:
   ```
   AUGUR_HOST=augur-db
   AUGUR_PORT=5432
   AUGUR_DATABASE=augur
   AUGUR_USERNAME=augur
   AUGUR_PASSWORD=augur
   AUGUR_SCHEMA=collection_data
   ```
2. Start it:
   ```
   docker compose up
   ```
   Docker pulls the image; on first boot it loads the data and exposes the DB on
   `localhost:5433`. Connecting directly:
   ```
   psql -h localhost -p 5433 -U augur -d augur   # password: augur
   ```

The data lives in the `collection_data` schema (the collectOSS schema name).

## For maintainers — rebuild & publish

The data dump is **never committed** (76MB, gitignored at
`docker/augur-db/init/03_data.sql`). It is baked into the published image only.

1. Place the Augur dump at `docker/augur-db/init/03_data.sql`.
2. Log in to GHCR (one-time, PAT needs `write:packages`):
   ```
   echo "$GHCR_PAT" | docker login ghcr.io -u <github-username> --password-stdin
   ```
3. Build and push:
   ```
   docker/augur-db/build-and-push.sh
   ```
4. First publish only: make the package public at
   `github.com/orgs/oss-aspen/packages` → `8knot-min-db` → Package settings.

## How initialization works

PostgreSQL runs files in `init/` alphabetically on first boot:

- `03_data.sql` — the dump; loads schema, data, and materialized views into `augur_data`.
- `04_rename_to_collection_data.sql` — renames the schema to `collection_data`
  (OID-safe; data is untouched).
