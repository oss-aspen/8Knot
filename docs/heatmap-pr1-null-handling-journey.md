# Heatmap PR1: NULL Metadata Handling Journey

## Background

**Branch**: `heatmap-pr1-enable-queries-minimal`

**Original Goal**: Re-enable the heatmap visualizations using new materialized views from the database instead of direct queries. This was meant to be a minimal change - just swapping out the query mechanism.

**Expected Outcome**: Heatmaps display with data from materialized views.

**Actual Outcome**: Heatmaps showed "No data available" and crashed with TypeErrors.

---

## The Initial Problem

After enabling the queries with materialized views, all three heatmap visualizations displayed:

```
No data available
```

### Error Logs Showed:

```
TypeError: can only concatenate str (not "NoneType") to str
```

**Location**: `df_file_clean()` function in all three heatmap files

**Failing line**:
```python
path_slice = repo_id + "-" + repo_path + "/" + repo_name + "/"
```

---

## Discovery: NULL Metadata in Database

Further investigation revealed warning logs:

```
cntrb-file-heatmap - Skipping repo 72192 with NULL metadata:
  repo_name='None', repo_path='None'
```

### The Root Cause:

The database contained repositories with **NULL values** for critical metadata:
- `repo_name` was NULL (converted to string `'None'`)
- `repo_path` was NULL (converted to string `'None'`)
- In some cases, these appeared as Python `None` instead of the string `'None'`

**Repository 72192** was one such example, and it was being selected as the default repository by `repo_dropdown()` because it happened to be `repo_ids[0]`.

---

## Why This Broke the Heatmaps

### The Cascade of Failures:

1. **Repo Selection**: `repo_dropdown()` blindly selected `repo_ids[0]` (repo 72192)
2. **Directory Dropdown Crash**: `directory_dropdown()` tried to process this repo and crashed when building the file path
3. **String Concatenation Error**: Cannot concatenate `str + None` in Python
4. **No Fallback**: No mechanism to skip invalid repos and select the next valid one
5. **Result**: User sees "No data available" or the visualization crashes entirely

### Additional Issues Discovered:

**Infinite Wait Loops**: When `repo_id` was Python `None`, callbacks would enter infinite loops:
```python
while not_cached := cf.get_uncached(func_name=rfq.__name__, repolist=[repo_id]):
    logging.warning(f"WAITING ON DATA TO BECOME AVAILABLE")
    time.sleep(0.5)
```

This would wait forever because `None` can't retrieve any cache data.

---

## Attempted Solutions (Trial and Error)

### Attempt 1: Fix Query Column Naming
**Hypothesis**: Maybe the column names from the query don't match what the code expects.

**Action**: Changed `pr_files_query.py` to use `pull_request_id AS pull_request` alias

**Result**: ❌ Didn't solve the NULL metadata issue, but was needed for consistency with PR2

---

### Attempt 2: Defensive Column Checks
**Hypothesis**: Maybe some columns are missing from the cached data.

**Action**: Added checks like:
```python
if "repo_name" in df.columns else None
```

**Result**: ❌ Columns existed, but contained NULL values

---

### Attempt 3: Return Original DataFrame on NULL
**Hypothesis**: Maybe we should just pass the data through and let downstream code handle it.

**Action**: Return `df` instead of empty DataFrame when NULLs detected

**Result**: ❌ Downstream code still crashed on string concatenation

---

### Attempt 4: Check `repo_id is None` After String Conversion
**Hypothesis**: We can check for None after converting to string.

**Action**:
```python
repo_id = str(df_file["repo_id"].iloc[0])
if not repo_name or not repo_path or repo_id is None:
    return df
```

**Result**: ❌ `str(None)` becomes `"None"`, so the check never triggered

---

### Attempt 5: Add None Checks Only in Callbacks
**Hypothesis**: Maybe we just need to prevent None from entering the pipeline.

**Action**: Added None checks in `directory_dropdown()` and graph callbacks

**Result**: ⚠️ Prevented infinite loops, but didn't solve the repo selection issue

---

## The Solution That Worked

### Multi-Layered NULL Handling

After examining PR2 and PR3 (which worked), we implemented NULL handling at **every critical layer**:

#### 1. Enhanced Repo Selection (`repo_dropdown`)
```python
def repo_dropdown(repo_ids):
    # ... build data_array ...

    # Find first repo with valid metadata
    default_repo = None
    for repo_id in repo_ids:
        try:
            df = cf.retrieve_from_cache(tablename=rfq.__name__, repolist=[repo_id])
            if not df.empty:
                repo_name = df["repo_name"].iloc[0] if "repo_name" in df.columns else None
                repo_path = df["repo_path"].iloc[0] if "repo_path" in df.columns else None
                # Check for both None AND string 'None'
                if repo_name and repo_path and repo_name != 'None' and repo_path != 'None':
                    default_repo = repo_id
                    break
        except Exception as e:
            continue

    # Fallback to first repo if none valid
    if default_repo is None:
        default_repo = repo_ids[0] if repo_ids else None

    return data_array, default_repo
```

**Why**: Automatically skip repos with NULL metadata and select the first valid one.

---

#### 2. None Check in `directory_dropdown`
```python
def directory_dropdown(repo_id):
    # Handle None repo_id case
    if repo_id is None:
        logging.warning(f"{VIZ_ID} DROPDOWN - repo_id is None")
        return ["Top Level Directory"], "Top Level Directory"

    # ... rest of function ...
```

**Why**: Prevent infinite wait loops when repo_id is None.

---

#### 3. NULL Metadata Validation in `directory_dropdown`
```python
def directory_dropdown(repo_id):
    # ... cache retrieval ...

    repo_name = df["repo_name"].iloc[0]
    repo_path = df["repo_path"].iloc[0]
    repo_id_raw = df["repo_id"].iloc[0]

    # Check BEFORE converting to string
    if not repo_name or not repo_path or repo_id_raw is None or repo_name == 'None' or repo_path == 'None':
        logging.warning(f"{VIZ_ID} DROPDOWN - Null or empty values in repo metadata")
        return ["Top Level Directory"], "Top Level Directory"

    repo_id = str(repo_id_raw)
    # ... rest of function ...
```

**Why**: Catch NULL values after cache retrieval, before attempting string operations.

---

#### 4. None Check in Graph Callbacks
```python
def cntrb_file_heatmap_graph(searchbar_repos, repo_id, directory, bot_switch):
    # Handle None repo_id case
    if repo_id is None:
        logging.warning(f"{VIZ_ID} - repo_id is None")
        return nodata_graph

    # ... rest of function ...
```

**Why**: Prevent crashes when no valid repo could be selected.

---

#### 5. NULL Metadata Validation in `df_file_clean`
```python
def df_file_clean(df_file: pd.DataFrame, df_file_cntbs: pd.DataFrame, ...):
    repo_name = df_file["repo_name"].iloc[0]
    repo_path = df_file["repo_path"].iloc[0]
    repo_id_raw = df_file["repo_id"].iloc[0]

    # Check for None or empty string values
    if not repo_name or not repo_path or repo_id_raw is None or repo_name == 'None' or repo_path == 'None':
        logging.warning(f"{VIZ_ID} - Null or empty values in repo metadata")
        return pd.DataFrame()  # Return EMPTY, not original

    repo_id = str(repo_id_raw)
    # ... string concatenation is now safe ...
```

**Why**: Last line of defense before string operations. Returns empty DataFrame to signal failure.

---

#### 6. Empty DataFrame Check in `process_data`
```python
def process_data(df_file, df_actions, df_file_cntbs, directory, bot_switch):
    df_file = df_file_clean(df_file, df_file_cntbs, bot_switch)

    # Check if df_file_clean returned early due to NULL values
    if df_file.empty:
        return pd.DataFrame()

    # ... rest of processing ...
```

**Why**: Propagate the failure signal up the call stack gracefully.

---

## Why This Was Absolutely Necessary

### Option 1: Without NULL Handling
**Result**: Heatmaps crash with TypeError or show "No data available"
- User cannot use the visualization at all
- PR1 fails its goal of re-enabling heatmaps

### Option 2: With NULL Handling
**Result**: Heatmaps work by automatically selecting valid repos
- User sees working visualizations
- Invalid repos are skipped automatically
- Graceful degradation when no valid repos exist

### The Verdict:

**NULL handling was required to make PR1 functional.** Without it, the heatmaps were completely broken due to data quality issues in the database.

---

## Alternative Approaches Considered

### 1. Fix the Database
**Proposal**: Update repo 72192 and other repos to have valid `repo_name` and `repo_path`

**Pros**:
- Cleaner code
- Addresses root cause

**Cons**:
- Requires database migration
- Might not be possible if data is genuinely unavailable
- Doesn't prevent future NULL values

**Verdict**: Not feasible for this PR

---

### 2. Filter at Query Level
**Proposal**: Exclude repos with NULL metadata from `repo-choices` entirely

**Pros**:
- Prevents NULL repos from appearing in dropdown
- Simpler code in visualization layer

**Cons**:
- Requires changes to repo selection mechanism
- Outside scope of heatmap-specific PR

**Verdict**: Could be done in a separate PR

---

### 3. Minimal NULL Check Only
**Proposal**: Just add NULL check in `df_file_clean` to prevent crash

**Pros**:
- Truly minimal change
- Prevents TypeError

**Cons**:
- User would still see "No data available" on first load
- User would have to manually select a valid repo
- Poor UX

**Verdict**: Insufficient - heatmaps would appear broken

---

## Lessons Learned

### 1. Database NULLs Are Represented Inconsistently
- Sometimes `None` (Python)
- Sometimes `'None'` (string)
- Must check for **both** forms

### 2. String Conversion Masks NULL Values
```python
repo_id = str(df["repo_id"].iloc[0])  # Converts None to "None"
if repo_id is None:  # This will NEVER be true!
```

**Solution**: Check for NULL **before** converting to string:
```python
repo_id_raw = df["repo_id"].iloc[0]
if repo_id_raw is None or repo_id_raw == 'None':
    # Handle NULL
repo_id = str(repo_id_raw)
```

### 3. Defense in Depth Required
Single-point NULL checking was insufficient. We needed checks at:
- UI layer (repo selection)
- Callback layer (None checks)
- Processing layer (data validation)
- Return value propagation (empty DataFrame signals)

### 4. Auto-Selection Improves UX
Rather than forcing users to manually skip invalid repos, auto-selecting the first valid repo provides a better experience.

---

## Final Implementation

**Files Modified**:
- `8Knot/pages/codebase/visualizations/cntrb_file_heatmap.py`
- `8Knot/pages/codebase/visualizations/contribution_file_heatmap.py`
- `8Knot/pages/codebase/visualizations/reviewer_file_heatmap.py`

**Total Changes**: +190 lines, -9 lines

**Testing**: Verified that heatmaps now display correctly and automatically skip repo 72192 (NULL metadata) in favor of the first valid repository.

---

## Conclusion

While NULL handling was not part of the original "minimal" scope for PR1, it became **absolutely necessary** to make the heatmaps functional. Without it, users would encounter:
- TypeErrors and crashes
- "No data available" messages
- Infinite wait loops
- Non-functional visualizations

The alternative would be to ship **broken heatmaps**, which defeats the purpose of the PR entirely.

**The only two viable options were**:
1. ✅ Implement comprehensive NULL handling (what we did)
2. ❌ Don't show the heatmaps at all (defeats PR purpose)

Therefore, NULL handling is a **necessary evil** for PR1 to achieve its stated goal of re-enabling the heatmaps.
