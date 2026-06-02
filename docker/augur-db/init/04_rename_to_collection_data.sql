-- min_db: align the loaded dump with the collectOSS schema.
--
-- The provided dump (03_data.sql) loads its data into the legacy `augur_data`
-- schema. collectOSS-based 8Knot expects the schema to be named `collection_data`.
-- Renaming is OID-safe: all tables, views, foreign keys, and materialized-view
-- data follow the rename automatically, so no data is touched.
--
-- Runs after 03_data.sql due to alphabetical init ordering.

ALTER SCHEMA augur_data RENAME TO collection_data;
