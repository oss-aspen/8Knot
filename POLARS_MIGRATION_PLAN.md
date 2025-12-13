# Polars Migration Plan

## Executive Summary

This document outlines the phased approach to migrate 8Knot's **core data processing** from Pandas to Polars for improved performance. The visualization layer will remain Pandas-based for Plotly/Dash compatibility.

### Architecture Pattern: "Polars Core, Pandas Edge"

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Database  ──►  Query Layer  ──►  Processing  ──►  Viz Layer  │
│                   (Polars)         (Polars)         (Pandas)    │
│                                                                 │
│   ┌─────────┐    ┌─────────┐     ┌─────────┐     ┌─────────┐   │
│   │ Augur   │───►│ pl.read │────►│ Polars  │────►│.to_pandas│   │
│   │   DB    │    │ _sql()  │     │ Exprs   │     │  + Plot  │   │
│   └─────────┘    └─────────┘     └─────────┘     └─────────┘   │
│                                                                 │
│   BENEFITS:                                                     │
│   • 2-10x faster data processing with Polars                    │
│   • Lazy evaluation & query optimization                        │
│   • Full Plotly/Dash compatibility (expects Pandas)             │
│   • Minimal conversion overhead (Arrow-based, near zero-copy)   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Before starting the migration, we first address existing Pandas anti-patterns to establish performance baselines and clean code.

---

## Phase 0: Fix Pandas Anti-Patterns (Pre-Migration) ✅ IN PROGRESS

**Goal:** Achieve 2-10x speedups with existing Pandas code before migration.

### 0.1 Remove `.iterrows()` (CRITICAL - 10-100x slower)

| File | Line | Status |
|------|------|--------|
| `8Knot/pages/contributors/visualizations/contrib_importance_over_time.py` | 471 | ⏳ Pending |

**Fix Strategy:** Use `np.cumsum()` + `np.searchsorted()` for threshold finding.

### 0.2 Vectorize `.apply()` Calls (31 occurrences - 5-50x slower)

**Priority: High Impact**
| File | Count | Complexity |
|------|-------|------------|
| `contrib_importance_over_time.py` | 1 | Complex (nested function) |
| `active_drifting_contributors.py` | 1 | Complex (stateful) |
| `pr_staleness.py` | 1 | Complex (stateful) |
| `issue_staleness.py` | 1 | Complex (stateful) |
| `pr_over_time.py` | 1 | Medium |
| `issues_over_time.py` | 1 | Medium |

**Priority: Medium Impact**
| File | Count | Complexity |
|------|-------|------------|
| `cntrb_file_heatmap.py` | 4 | Low (list ops) |
| `reviewer_file_heatmap.py` | 4 | Low (list ops) |
| `contribution_file_heatmap.py` | 3 | Low (list ops) |
| `project_velocity.py` | 3 | Low (math.log) |
| `repo_general_info.py` | 1 | Low (timedelta.days) |

**Priority: Lower Impact**
| File | Count | Complexity |
|------|-------|------------|
| `pr_assignment.py` | 1 | Medium |
| `issue_assignment.py` | 1 | Medium |
| `pr_review_response.py` | 1 | Medium |
| `pr_first_response.py` | 1 | Medium |
| `cntrib_issue_assignment.py` | 1 | Medium (loop) |
| `cntrb_pr_assignment.py` | 1 | Medium (loop) |
| `gh_org_affiliation.py` | 2 | Complex (fuzzy match) |
| `augur_manager.py` | 2 | Low |

### 0.3 Remove `inplace=True` (16 files - Technical Debt)

| File | Status |
|------|--------|
| `preprocessing_utils.py` | ⏳ Pending |
| `cntrb_file_heatmap.py` | ⏳ Pending |
| `reviewer_file_heatmap.py` | ⏳ Pending |
| `contribution_file_heatmap.py` | ⏳ Pending |
| `contrib_importance_pie.py` (2 files) | ⏳ Pending |
| `ossf_scorecard.py` | ⏳ Pending |
| `code_languages.py` | ⏳ Pending |
| `new_contributor.py` | ⏳ Pending |
| `first_time_contributions.py` | ⏳ Pending |
| `contributors_types_over_time.py` | ⏳ Pending |
| `contrib_drive_repeat.py` | ⏳ Pending |
| `active_drifting_contributors.py` | ⏳ Pending |
| `commits_over_time.py` | ⏳ Pending |
| `project_velocity.py` | ⏳ Pending |
| `augur_manager.py` | ⏳ Pending |

---

## Phase 1: Preparation

**Goal:** Set up infrastructure for Polars migration.

### 1.1 Add Polars to Dependencies
```toml
# pyproject.toml
polars = "~1.0"
```

### 1.2 Create Performance Benchmarks
- Measure current query execution times
- Identify slowest visualization modules
- Create automated benchmark suite

### 1.3 Build DataFrame Adapter Layer
```python
# 8Knot/utils/dataframe_adapter.py
import polars as pl
import pandas as pd
from typing import Union

DataFrameLike = Union[pd.DataFrame, pl.DataFrame]

def to_polars(df: pd.DataFrame) -> pl.DataFrame:
    """Convert Pandas DataFrame to Polars for processing."""
    return pl.from_pandas(df)

def to_pandas(df: pl.DataFrame) -> pd.DataFrame:
    """Convert Polars DataFrame to Pandas for visualization."""
    return df.to_pandas()

def process_with_polars(df: pd.DataFrame, processor: callable) -> pd.DataFrame:
    """
    Wrapper for Polars processing with automatic Pandas conversion.

    Usage:
        def my_processor(pl_df: pl.DataFrame) -> pl.DataFrame:
            return pl_df.filter(pl.col("x") > 0)

        result = process_with_polars(pandas_df, my_processor)
        # result is a Pandas DataFrame ready for Plotly
    """
    pl_df = to_polars(df)
    result = processor(pl_df)
    return to_pandas(result)
```

### 1.4 Update Cache Layer
- Modify Feather serialization to handle both Pandas and Polars
- Leverage Arrow format (already used) for zero-copy conversion

---

## Phase 2: Pilot Conversion

**Goal:** Validate approach with low-risk modules.

### 2.1 Target Modules (Start Simple)
1. `repo_general_info.py` - Simple, isolated
2. `code_languages.py` - Minimal dependencies
3. `ossf_scorecard.py` - Read-heavy, good benchmark candidate

### 2.2 Conversion Pattern
```python
# Before (Pandas)
df = pd.DataFrame(data)
df["new_col"] = df["old_col"].apply(lambda x: x * 2)

# After (Polars)
df = pl.DataFrame(data)
df = df.with_columns(
    (pl.col("old_col") * 2).alias("new_col")
)
```

### 2.3 Validation
- Compare outputs between Pandas and Polars versions
- Measure performance improvement
- Document API differences

---

## Phase 3: Query Layer Migration

**Goal:** Convert data ingestion for maximum impact.

### 3.1 Priority Order
1. `augur_manager.py` - Central data access
2. Query files in `8Knot/queries/`
3. Cache manager integration

### 3.2 Lazy Evaluation
- Use `pl.scan_*` for lazy loading
- Chain operations before `.collect()`
- Reduce memory footprint

---

## Phase 4: Visualization Module Migration

**Goal:** Convert data processing in visualization modules to Polars, keeping Pandas at the boundary.

### 4.1 Migration Order (by complexity)
1. **Simple:** repo_overview visualizations
2. **Medium:** contributions visualizations
3. **Complex:** contributors visualizations
4. **Complex:** codebase heatmaps

### 4.2 Module Conversion Pattern

Each visualization module follows this pattern:

```python
# BEFORE: All Pandas
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["status"] == "active"]
    df = df.groupby("category").agg({"value": "sum"})
    return df  # Pandas DataFrame for Plotly

# AFTER: Polars processing, Pandas at boundary
def process_data(df: pd.DataFrame) -> pd.DataFrame:
    # Convert to Polars for fast processing
    pl_df = pl.from_pandas(df)

    # All heavy processing in Polars (2-10x faster)
    pl_df = (
        pl_df.lazy()
        .filter(pl.col("status") == "active")
        .group_by("category")
        .agg(pl.col("value").sum())
        .collect()
    )

    # Convert back to Pandas for Plotly/Dash
    return pl_df.to_pandas()
```

### 4.3 Polars-Specific Optimizations
- Use `.lazy()` for query optimization
- Leverage multi-threading automatically
- Use native Polars expressions over UDFs
- Chain operations for optimal query planning

---

## Phase 5: Optimization & Finalization

**Goal:** Optimize the hybrid Polars/Pandas architecture.

### 5.1 Keep Pandas for Visualization Layer
- **Plotly/Dash requires Pandas DataFrames** - this is a hard requirement
- Pandas remains in dependencies for visualization compatibility
- Conversion overhead is minimal (Arrow-based, near zero-copy)

### 5.2 Optimize Conversion Points
- Minimize Polars→Pandas conversions (do once at the end)
- Use Arrow interchange for zero-copy where possible
- Profile to ensure conversion isn't a bottleneck

### 5.3 Advanced Polars Optimizations
- Streaming for large datasets (`pl.scan_*` → `.collect(streaming=True)`)
- Expression optimization with lazy evaluation
- Memory-mapped files for huge datasets
- Parallel query execution

---

## Performance Targets

| Metric | Current (Pandas) | Target (Polars) |
|--------|------------------|-----------------|
| Query execution | Baseline | 2-5x faster |
| Memory usage | Baseline | 50% reduction |
| Visualization load | Baseline | 3-10x faster |

---

## Anti-Pattern Fixes: Implementation Details

### Fix: `.iterrows()` → Vectorized Cumsum

**Before:**
```python
running_sum = 0
for _, row in df.iterrows():
    running_sum += row[action_type]
    lottery_factor += 1
    if running_sum >= thresh_cntrbs:
        break
return lottery_factor
```

**After:**
```python
cumsum = df[action_type].cumsum()
idx = np.searchsorted(cumsum.values, thresh_cntrbs, side='right')
return min(idx + 1, len(df))
```

### Fix: `.apply(lambda x: x.days)` → `.dt.days`

**Before:**
```python
df["time_bt_release"] = df["time_bt_release"].apply(lambda x: x.days)
```

**After:**
```python
df["time_bt_release"] = df["time_bt_release"].dt.days
```

### Fix: `inplace=True` → Chained Assignment

**Before:**
```python
df.rename(columns={"action": "Action"}, inplace=True)
df.drop("index", axis=1, inplace=True)
```

**After:**
```python
df = df.rename(columns={"action": "Action"})
df = df.drop(columns=["index"])
```

---

## Timeline Estimate

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0: Anti-patterns | 1-2 days | 🔄 In Progress |
| Phase 1: Preparation | 1 day | ⏳ Pending |
| Phase 2: Pilot | 2-3 days | ⏳ Pending |
| Phase 3: Query Layer | 3-5 days | ⏳ Pending |
| Phase 4: Visualizations | 5-7 days | ⏳ Pending |
| Phase 5: Optimization | 1-2 days | ⏳ Pending |

**Total Estimated Duration:** 2-3 weeks

### Key Milestones
- **M1:** Anti-patterns fixed, baseline established
- **M2:** Polars added, adapter layer working
- **M3:** First module fully converted and benchmarked
- **M4:** Query layer migrated (biggest performance gain)
- **M5:** All visualization modules use Polars core + Pandas edge

---

## Success Criteria

### Phase 0 (Anti-Patterns)
1. ✅ All `.iterrows()` removed
2. ✅ All `.apply()` vectorized where possible
3. ✅ All `inplace=True` removed

### Final State
4. ✅ Polars used for all core data processing
5. ✅ Pandas used only at visualization boundary (Plotly/Dash compatibility)
6. ✅ 2x+ performance improvement measured
7. ✅ All tests passing
8. ✅ No regressions in visualization output
9. ✅ Conversion overhead < 5% of total processing time
