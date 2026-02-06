# Heatmap Visualization Specification

## Overview

This document outlines the specification for the codebase heatmap visualizations displayed at `localhost:8080/codebase`. The goal is to create a simplified, maintainable implementation that efficiently displays file-level activity data.

## Problem Statement

The previous implementation was overly complex due to:
- Multiple data sources per visualization (3 queries each)
- Complex client-side data joins
- Cascading cache-wait loops causing delays
- Duplicated code across all three heatmaps
- No proper null/error handling

## Solution Overview

### Design Principles

1. **Single Responsibility** - Each function does one thing well
2. **DRY (Don't Repeat Yourself)** - Shared utilities for common operations
3. **Graceful Degradation** - Handle nulls and missing data elegantly
4. **Simplicity** - Minimal processing, let SQL do heavy lifting

## Visualizations

### 1. Contribution File Heatmap
- **Purpose**: Show PR activity (opened/merged) per file/directory over time
- **X-axis**: Time (months)
- **Y-axis**: Files/directories
- **Color**: Count of PRs
- **Data Sources**: `repo_files_query`, `pr_files_query`, `prs_query`

### 2. Contributor File Heatmap
- **Purpose**: Show when contributors who touched files were last active
- **X-axis**: Time (months)
- **Y-axis**: Files/directories
- **Color**: Count of "last seen" contributors
- **Data Sources**: `repo_files_query`, `cntrb_per_file_query`, `contributors_query`

### 3. Reviewer File Heatmap
- **Purpose**: Show when reviewers of file PRs were last active
- **X-axis**: Time (months)
- **Y-axis**: Files/directories
- **Color**: Count of "last seen" reviewers
- **Data Sources**: `repo_files_query`, `cntrb_per_file_query`, `contributors_query`

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      codebase.py (layout)                       │
├─────────────────────────────────────────────────────────────────┤
│  - gc_contribution_file_heatmap                                 │
│  - gc_cntrb_file_heatmap                                        │
│  - gc_reviewer_file_heatmap                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            visualizations/*.py (individual heatmaps)            │
├─────────────────────────────────────────────────────────────────┤
│  - UI Component (Card with graph + controls)                    │
│  - Callbacks (repo dropdown, directory dropdown, graph)         │
│  - process_data() - visualization-specific processing           │
│  - create_figure() - create Plotly figure                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    heatmap_utils.py (shared)                    │
├─────────────────────────────────────────────────────────────────┤
│  - wait_for_cache() - unified cache waiting                     │
│  - get_repo_files_df() - retrieve and clean file data           │
│  - get_directories() - extract directory list from files        │
│  - clean_file_path() - normalize file paths                     │
│  - aggregate_by_directory() - group files by directory level    │
│  - create_heatmap_figure() - common figure creation             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      queries/*.py (data)                        │
├─────────────────────────────────────────────────────────────────┤
│  - repo_files_query                                             │
│  - cntrb_per_file_query                                         │
│  - contributors_query                                           │
│  - prs_query                                                    │
│  - pr_files_query                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Shared Utilities (heatmap_utils.py)

### Functions

```python
def wait_for_cache(query_func, repolist: list, timeout: int = 300) -> bool:
    """Wait for cache data to become available with timeout."""

def get_repo_files_df(repo_id: int) -> pd.DataFrame:
    """Retrieve and clean repo files data with null handling."""

def get_directories(df: pd.DataFrame) -> list:
    """Extract sorted list of directories from file dataframe."""

def clean_file_path(df: pd.DataFrame, repo_name: str, repo_path: str, repo_id: str) -> pd.DataFrame:
    """Normalize file paths by removing repo prefix."""

def aggregate_by_directory(df: pd.DataFrame, directory: str, value_column: str) -> pd.DataFrame:
    """Group data by directory level and aggregate values."""

def create_heatmap_figure(df: pd.DataFrame, color_label: str, height: int = 700) -> go.Figure:
    """Create consistent heatmap figure with standard styling."""
```

## Controls

Each heatmap includes:
1. **Repository Selector** - Dropdown to select which repo to analyze
2. **Directory Selector** - Dropdown to drill into subdirectories
3. **About Graph Button** - Popover with visualization description

### Contribution Heatmap Additional Controls
- **Graph View Toggle** - Switch between "PR Opened" and "PR Merged"

## Error Handling

### Null Value Handling
```python
# Check for None before string operations
if df["repo_name"].iloc[0] is None:
    return nodata_graph

# Safe null handling in aggregations
df["value"].fillna(0, inplace=True)

# Return nodata_graph when data is missing
if df.empty:
    return nodata_graph
```

### Cache Timeout
```python
# Prevent infinite wait loops
max_wait_time = 300  # 5 minutes
start_time = time.time()
while not_cached := cf.get_uncached(...):
    if time.time() - start_time > max_wait_time:
        logging.error("Cache timeout exceeded")
        return nodata_graph
    time.sleep(0.5)
```

## Data Flow

### Standard Callback Pattern
```python
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [Input("repo-choices", "data"), Input(f"repo-{PAGE}-{VIZ_ID}", "value"), ...],
    background=True,
)
def heatmap_graph(repolist, repo_id, directory, ...):
    # 1. Wait for cache with timeout
    if not wait_for_cache(query_func, [repo_id]):
        return nodata_graph

    # 2. Retrieve data
    df = cf.retrieve_from_cache(tablename=query_func.__name__, repolist=[repo_id])

    # 3. Validate data
    if df.empty:
        return nodata_graph

    # 4. Process data
    df_processed = process_data(df, directory, ...)

    # 5. Create and return figure
    return create_figure(df_processed)
```

## File Structure

```
8Knot/pages/codebase/
├── __init__.py
├── codebase.py                          # Layout
└── visualizations/
    ├── __init__.py
    ├── heatmap_utils.py                 # NEW: Shared utilities
    ├── cntrb_file_heatmap.py            # Contributor heatmap
    ├── contribution_file_heatmap.py     # PR activity heatmap
    └── reviewer_file_heatmap.py         # Reviewer heatmap
```

## Testing Checklist

- [ ] All three heatmaps load without errors
- [ ] Repository dropdown populates correctly
- [ ] Directory dropdown populates based on selected repo
- [ ] Heatmap renders with color gradient
- [ ] nodata_graph displays when no data available
- [ ] Null values don't cause crashes
- [ ] Cache timeout works correctly
- [ ] Graph View toggle works (contribution heatmap)

## Implementation Order

1. Create `heatmap_utils.py` with shared functions
2. Refactor `contribution_file_heatmap.py` (simplest - only PR data)
3. Refactor `cntrb_file_heatmap.py`
4. Refactor `reviewer_file_heatmap.py`
5. Update `codebase.py` layout
6. Test all visualizations
