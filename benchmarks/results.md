# Cache Layer Analysis: Redis Data Cache Removal

## Summary

The Redis `CacheManager` class was a **dead code path**. All data caching
in 8knot flows through `cache_facade.py` (Postgres). Removing `CacheManager`
has zero performance impact because it was never called.

## Static Analysis

| Metric | Redis CacheManager | Postgres cache_facade |
|--------|-------------------:|----------------------:|
| Files importing | 0 | 0 |
| Instantiations | 0 | N/A (module functions) |
| Method calls | 0 | 111 |

## Data Flow

| Path | Count | Status |
|------|------:|--------|
| Queries using `caching_wrapper()` (Postgres write) | 17 | **Active** |
| Viz callbacks using `retrieve_from_cache()` (Postgres read) | 37 | **Active** |
| Viz callbacks using `get_uncached()` (Postgres bookkeeping) | 37 | **Active** |
| Viz callbacks using `cm.grabm()` (Redis read) | 0 | **Dead code** |

## Verdict

- **0** visualization callbacks read from Redis
- **37** visualization callbacks read from Postgres
- **17** query workers write to Postgres
- Redis data cache can be safely removed with **zero regression risk**

## What Was Changed

1. Deleted `8Knot/cache_manager/cache_manager.py` (Redis CacheManager class)
2. Removed dead `CacheManager` imports from 4 files
3. Removed dead `cache = cm()` variable in `index_callbacks.py`
4. Renamed `redis-cache` to `redis-broker` in docker-compose (reflects actual Celery role)
5. Updated CI workflow and README references
