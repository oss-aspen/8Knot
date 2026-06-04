The SQL tables referenced by 8Knot queries:
  - repo → Aveloxis: repos
  - repo_groups → Aveloxis: repo_groups (same)
  - pull_requests → Aveloxis: pull_requests (same)
  - pull_request_events → Aveloxis: pull_request_events (same)
  - pull_request_message_ref → Aveloxis: pull_request_message_ref (same)
  - commits → Aveloxis: commits (same)
  - issues → Aveloxis: issues (same)
  - repo_deps_scorecard → Aveloxis: repo_deps_scorecard (same)
  - repo_deps_libyear → Aveloxis: repo_deps_libyear (same)
  - repo_info → Aveloxis: repo_info (same)
  - contributors_aliases → Aveloxis: contributors_aliases (same)
  - contributors → Aveloxis: contributors (same)
  - explorer_repo_languages → materialized view (same)
  - explorer_* → materialized views (same)
  - repo_labor → Aveloxis: repo_labor (same)

  Only one table name differs: repo → repos. Let me also check the _bots.py file:

  Read 1 file (ctrl+o to expand)

⏺ Uses contributors c — that name is the same. Now let me check ALL uses of repo r or FROM repo across the full codebase to find every
  place that needs repo → repos:

  Searched for 1 pattern (ctrl+o to expand)

⏺ Also check the SQL matview files for repo references:

  Searched for 2 patterns (ctrl+o to expand)

⏺ Good. Every repo reference (without _) in SQL contexts needs to become repos. Let me do all the changes now. I'll use replace_all
  carefully — I need to replace repo only where it's used as a table name, not in column names like repo_id, repo_name, repo_git.

  The pattern: replace repo r with repos r, FROM repo with FROM repos, JOIN repo with JOIN repos, repo.repo_ with repos.repo_, and
  standalone repo (table reference in FROM clause) with repos.

trl+o to expand)                                                                                                       
                                                                                                                                          
⏺ 18 files changed. Two categories of changes:
                                                                                                                                          
  1. Schema prefix removal (from earlier): Removed augur_data. from all SQL queries so they use search_path from AUGUR_SCHEMA env var     
  2. Table rename (just now): repo → repos everywhere — the only table name that differs between Augur and Aveloxis
                                                                                                                                          
  The queries now use unqualified table names (repos, pull_requests, commits, etc.) which PostgreSQL resolves via                         
  search_path=aveloxis_data set at connection time.   