# sample_collected_data — ready-to-use local database

A pre-populated PostgreSQL image with sample collected data baked in, so you can
run 8Knot or notebooks locally without access to a remote collectOSS/Augur
instance. You never build it — `docker compose up` pulls the published image.

Published image: `ghcr.io/oss-aspen/sample-collected-data:latest` (public).

## Usage

1. In your `.env`, point 8Knot at the local DB:
   ```
   AUGUR_HOST=sample-collected-data
   AUGUR_PORT=5432
   AUGUR_DATABASE=sample_collected_data
   AUGUR_USERNAME=sample_user
   AUGUR_PASSWORD=sample_password
   AUGUR_SCHEMA=data,augur_data
   ```
2. Start it:
   ```
   docker compose up
   ```
   Docker pulls the image and exposes the DB on `localhost:5433`. Connect directly:
   ```
   psql -h localhost -p 5433 -U sample_user -d sample_collected_data
   ```

The data lives in the `data` schema (the collectOSS schema name).
