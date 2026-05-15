# End-Of-Life Source Investigation

Two public data sources are useful starting points for determining whether a
repository depends on software with a known end-of-life date:

- https://endoflife.date/
- https://endoflife.software/

Recommended approach:

1. Pull both source catalogs into a normalized product table.
2. Normalize ecosystem names, product slugs, release names, and version ranges.
3. Deduplicate products that appear in both catalogs.
4. Join detected repository dependencies against the normalized product table.
5. Keep source provenance so visualizations can explain which catalog supplied
   each lifecycle status.

Open implementation questions:

- Some repositories declare runtime versions in package manifests, while others
  use container images, CI files, or documentation. The detector should likely
  combine multiple file sources.
- The catalogs do not always use the same product naming, so exact matching is
  not enough for high-confidence results.
- A future visualization should distinguish "known EOL", "not EOL", and
  "unknown because no supported source matched".
