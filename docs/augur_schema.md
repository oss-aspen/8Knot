# Augur Schema References

8Knot query modules read from Augur-managed tables, so schema changes should be
checked against Augur's upstream documentation before changing SQL.

Primary references:

- Augur documentation: https://oss-augur.readthedocs.io/
- Augur repository: https://github.com/chaoss/augur
- Augur schema files: https://github.com/chaoss/augur/tree/main/augur/application/db/schema

When adding or editing a query in `8Knot/queries`, include the table and column
names in the query docstring if they are not obvious from the visualization
name. For materialized views in `docs/materialized_views`, include a short note
about the Augur tables the view depends on.
