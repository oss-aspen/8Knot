# Graph Report - /Users/cfonseca/Documents/GitHub/8knot-dev  (2026-04-27)

## Corpus Check
- 175 files · ~120,221 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 845 nodes · 1515 edges · 29 communities detected
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 390 edges (avg confidence: 0.73)
- Token cost: 12,500 input · 3,200 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core Application & Entry Points|Core Application & Entry Points]]
- [[_COMMUNITY_Code Visualization & Heatmaps|Code Visualization & Heatmaps]]
- [[_COMMUNITY_Data Queries & Cache Layer|Data Queries & Cache Layer]]
- [[_COMMUNITY_Search & State Management|Search & State Management]]
- [[_COMMUNITY_Contributions & Issue Tracking|Contributions & Issue Tracking]]
- [[_COMMUNITY_Documentation & Project Governance|Documentation & Project Governance]]
- [[_COMMUNITY_UI Layout & Search Utilities|UI Layout & Search Utilities]]
- [[_COMMUNITY_Authentication & User Groups|Authentication & User Groups]]
- [[_COMMUNITY_Contributor Behavior Analytics|Contributor Behavior Analytics]]
- [[_COMMUNITY_Organization Affiliation Analysis|Organization Affiliation Analysis]]
- [[_COMMUNITY_Navigation Components|Navigation Components]]
- [[_COMMUNITY_Landing Page & Onboarding|Landing Page & Onboarding]]
- [[_COMMUNITY_Repository Overview|Repository Overview]]
- [[_COMMUNITY_Contributor Type Classification|Contributor Type Classification]]
- [[_COMMUNITY_UI Assets & Branding|UI Assets & Branding]]
- [[_COMMUNITY_CHAOSS Metrics|CHAOSS Metrics]]
- [[_COMMUNITY_Plotly Visualization Features|Plotly Visualization Features]]
- [[_COMMUNITY_Database Initialization|Database Initialization]]
- [[_COMMUNITY_Chart Asset Library|Chart Asset Library]]
- [[_COMMUNITY_System Architecture Components|System Architecture Components]]
- [[_COMMUNITY_PR First Response Metrics|PR First Response Metrics]]
- [[_COMMUNITY_PR Review Response Metrics|PR Review Response Metrics]]
- [[_COMMUNITY_Issue Assignment Metrics|Issue Assignment Metrics]]
- [[_COMMUNITY_User Group Management UI|User Group Management UI]]
- [[_COMMUNITY_8Knot Branding Assets|8Knot Branding Assets]]
- [[_COMMUNITY_Module Init Files|Module Init Files]]
- [[_COMMUNITY_Search Type Detection|Search Type Detection]]
- [[_COMMUNITY_Nav Collapse Callback|Nav Collapse Callback]]
- [[_COMMUNITY_Pages Overview Docs|Pages Overview Docs]]

## God Nodes (most connected - your core abstractions)
1. `AugurManager` - 62 edges
2. `get_uncached()` - 44 edges
3. `retrieve_from_cache()` - 42 edges
4. `VisualizationAIO` - 36 edges
5. `CacheManager` - 35 edges
6. `8Knot Application` - 25 edges
7. `caching_wrapper()` - 22 edges
8. `get_graph_time_values()` - 19 edges
9. `contributors_df_action_naming()` - 14 edges
10. `DropdownNavItemAIO` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Redis Memory Overcommit Production Guidelines` --conceptually_related_to--> `8Knot Application`  [INFERRED]
  PRODUCTION_GUIDELINES.md → README.md
- `macOS Setup Instructions` --conceptually_related_to--> `8Knot Application`  [INFERRED]
  osx-instructions.md → README.md
- `(Worker Query)     Executes SQL query against Augur frontend for logged-in user'` --uses--> `CacheManager`  [INFERRED]
  /Users/cfonseca/Documents/GitHub/8knot-dev/8Knot/queries/user_groups_query.py → /Users/cfonseca/Documents/GitHub/8knot-dev/8Knot/cache_manager/cache_manager.py
- `Requests all user-level groups from augur frontend.      Args:         username` --uses--> `CacheManager`  [INFERRED]
  /Users/cfonseca/Documents/GitHub/8knot-dev/8Knot/queries/user_groups_query.py → /Users/cfonseca/Documents/GitHub/8knot-dev/8Knot/cache_manager/cache_manager.py
- `Converts repo_git URLs to     indexed repo_ids from startup for consumption` --uses--> `CacheManager`  [INFERRED]
  /Users/cfonseca/Documents/GitHub/8knot-dev/8Knot/queries/user_groups_query.py → /Users/cfonseca/Documents/GitHub/8knot-dev/8Knot/cache_manager/cache_manager.py

## Hyperedges (group relationships)
- **8Knot Multi-Container Deployment Stack** — readme_app_py, readme_celery_py, readme_podman, readme_docker [INFERRED 0.85]
- **Augur OAuth2.0 Integration Flow** — readme_login_py, user_accounts_redis_session, user_accounts_flask_login, readme_augur [EXTRACTED 0.90]
- **CI and Nightly Automated Testing Pipeline** — ci_testing_guide, nightly_dependency_testing, nightly_health_endpoint, ci_pr_build_test_workflow [INFERRED 0.85]

## Communities

### Community 0 - "Core Application & Entry Points"
Cohesion: 0.05
Nodes (61): health_check(), README -- Organization of Callback Functions  In an effort to compartmentalize o, Simple health check endpoint for CI/CD testing, AugurManager, Runs SQL query against our Augur database.          Args:         -----, Handles connection and queries to Augur database.      Attributes:     ---------, Creates _engine.Engine object connected to our Augur database.          Returns:, get_bots_list() (+53 more)

### Community 1 - "Code Visualization & Heatmaps"
Cohesion: 0.05
Nodes (64): Getter method for dictionary         that converts a repo_id to the respective, get_uncached(), Checks bookkeeping data to find, for a given querying function, which     repos', Sets redis value as data at name=hash(func, repo)          Args:             fun, cntrb_file_heatmap_graph(), cntrb_per_directory_value(), cntrb_to_last_activity(), create_figure() (+56 more)

### Community 2 - "Data Queries & Cache Layer"
Cohesion: 0.03
Nodes (43): affiliation_query(), (Worker Query)     Executes SQL query against Augur database for organization af, cache_query_results(), caching_wrapper(), This file contains the interface by which application code accesses with the pos, Combines steps of (1) identifying which repos aren't already cached and     (2), For a given table in cache, get all results     that having a matching repo_id., Runs {query} against primary database specified by {db_connection_string} with v (+35 more)

### Community 3 - "Search & State Management"
Cohesion: 0.05
Nodes (52): Returns the list of repos in an org.          Args:             org (str): Githu, Checks if org name in set of known org names          Args:             org (str, Getter method for the initial multiselect option.             May be overwritten, Getter method on all entries in repo+orgs options         for the multiselect dr, CacheManager, Sets many redis value as data at name=hash(func, repo)          Args:, Gets many redis value as data at name=hash(func, repo)          Args:, Checks whether key is in Redis for hash(func, repo)          Args:             f (+44 more)

### Community 4 - "Contributions & Issue Tracking"
Cohesion: 0.06
Nodes (45): cntrib_pr_assignment_graph(), create_figure(), pr_assignment(), process_data(), This function takes a start and an end date and determines how many     prs that, cntrib_issue_assignment_graph(), create_figure(), issue_assignment() (+37 more)

### Community 5 - "Documentation & Project Governance"
Cohesion: 0.05
Nodes (50): Augur Admin Role, Augur Deployer Role, Augur Login Setup Guide, Augur User Role, Cali Dolfi (Maintainer), James Kunstle (Maintainer), pr-build-test.yml GitHub Actions Workflow, CI Testing Guide (+42 more)

### Community 6 - "UI Layout & Search Utilities"
Cohesion: 0.09
Nodes (37): calculate_token_score(), clean_repo_name(), create_alert(), create_bot_filter_switch(), create_bottom_navbar(), create_button(), create_multiselect_styles(), create_search_bar() (+29 more)

### Community 7 - "Authentication & User Groups"
Cohesion: 0.09
Nodes (24): Getter method for dictionary         that converts a git URL to the respective, Large parts of code written by John McGinness, University of Missouri          R, Large parts of code written by John McGinness, University of Missouri         Ad, Large parts of code written by John McGinness, University of Missouri         Ad, Large parts of code written by John McGinness, University of Missouri         Ad, Get redis value as data at name=hash(func, repo)          Args:             func, configure_server_login(), get_admin_groups() (+16 more)

### Community 8 - "Contributor Behavior Analytics"
Cohesion: 0.12
Nodes (20): active_drifting_contributors_graph(), create_figure(), get_active_drifting_away_up_to(), process_data(), create_figure(), graph_title(), process_data(), repeat_drive_by_graph() (+12 more)

### Community 9 - "Organization Affiliation Analysis"
Cohesion: 0.12
Nodes (20): commit_domains_graph(), create_figure(), process_data(), # TODO: create docstring, create_figure(), fuzzy_match(), gh_org_affiliation_graph(), process_data() (+12 more)

### Community 10 - "Navigation Components"
Cohesion: 0.15
Nodes (19): DropdownNavItemAIO, Creates a clickable section in the sidebar, which allows navigation to a page an, toggle_collapses_dynamically(), create_app_stores(), create_main_content_area(), create_main_layout(), create_sidebar(), create_sidebar_navigation() (+11 more)

### Community 11 - "Landing Page & Onboarding"
Cohesion: 0.12
Nodes (12): create_definition_item(), Create a standardized definition item for the definitions section.      Args:, Toggle the visibility of welcome content and rotate the button icon., Update the main content and navigation title based on the selected landing page, toggle_welcome_content(), update_main_tab_content(), create_landing_hero(), create_welcome_content() (+4 more)

### Community 12 - "Repository Overview"
Cohesion: 0.15
Nodes (13): code_languages_graph(), create_figure(), graph_title(), process_data(), ossf_scorecard(), toggle_popover(), package_version_graph(), multi_query_helper() (+5 more)

### Community 13 - "Contributor Type Classification"
Cohesion: 0.2
Nodes (12): contrib_activity_cycle_graph(), create_figure(), process_data(), calc_lottery_factor(), cntrb_prolificacy_over_time(), create_contrib_prolificacy_over_time_graph(), create_figure(), graph_title() (+4 more)

### Community 14 - "UI Assets & Branding"
Cohesion: 0.15
Nodes (17): Affiliation Feature / Page, Affiliation / Layers Icon, CHAOSS Logo (full wordmark), CHAOSS Project, CHAOSS Small Logo (compact), Codebase Feature / Page, Codebase / Code File Icon, Contributions Feature / Page (+9 more)

### Community 15 - "CHAOSS Metrics"
Cohesion: 0.29
Nodes (7): create_figure(), create_top_k_cntrbs_graph(), graph_title(), process_data(), create_figure(), process_data(), project_velocity_graph()

### Community 16 - "Plotly Visualization Features"
Cohesion: 0.25
Nodes (15): Contributor Activity Chart (Active/Drifting/Away), Issue Staleness Chart (New/Staling/Stale), Plotly Legend Toggle Feature, Plotly Toolbar, Plotly Zoom Interaction Feature, All Categories Graph (New/Staling/Stale Legend), Click-Zoom Interaction Graph (Selection Box Overlay), Graph Wide Shot (Contributors Over Time, Active/Drifting/Away) (+7 more)

### Community 17 - "Database Initialization"
Cohesion: 0.32
Nodes (10): _connect_with_retry(), _create_application_database(), _create_application_tables(), db_init(), NOTES ABOUT THIS FILE:  This file uses raw SQL to create tables in Postgres. It', On fresh application boot, Postgres is fresh, so     database where we cache dat, Creates tables for cached data in 'augur_cache' database.      Tables created:, # TODO: timestamps being stored as strings- don't need to do that anymore. (+2 more)

### Community 18 - "Chart Asset Library"
Cohesion: 0.29
Nodes (11): Contributor Type: New, Contributor Type: Stale, Contributor Type: Staling, Focus Area Chart - Time Series with Selection Box, Focus Group Chart - Full Range Bar Chart with Area Selection, Legend Chart - Contributor Type Time Series Full Range, Legend Selected Chart - Contributor Type Time Series Single Repo, Right Arrow Icon - Navigation UI Element (+3 more)

### Community 19 - "System Architecture Components"
Cohesion: 0.61
Nodes (8): Application Server (Software), 8Knot Architecture Diagram - Application Server Task Queue Celery Workers Augur DB, Augur Database, Celery Data Collection Workers, Celery Data Processing Workers, Data Cache (Redis), 8Knot Works Diagram - Application Server Task Queue Celery Data Collection Workers Augur DB, Task Queue (Redis)

### Community 20 - "PR First Response Metrics"
Cohesion: 0.57
Nodes (5): create_figure(), get_open_response(), pr_first_response_graph(), process_data(), This function takes a date and determines how many     prs in that time interval

### Community 21 - "PR Review Response Metrics"
Cohesion: 0.57
Nodes (5): create_figure(), get_open_response(), pr_review_response_graph(), process_data(), This function takes a date and determines how many prs in that time interval are

### Community 22 - "Issue Assignment Metrics"
Cohesion: 0.57
Nodes (5): cntrib_issue_assignment_graph(), create_figure(), issue_assignment(), process_data(), This function takes a start and a end date and determines how many     issues in

### Community 23 - "User Group Management UI"
Cohesion: 0.43
Nodes (7): Add Repos to Group Form, GitHub Repo or Org Group Search UI, New Group Name Input Form, 8Knot Logged-In Navigation Bar, 8Knot Login Button (Augur log in/sign up), Augur Authorize App OAuth Screen, Augur User Registration Form

### Community 24 - "8Knot Branding Assets"
Cohesion: 0.67
Nodes (4): 8Knot Brand / Application Identity, Robot Head Icon - AI or Machine Learning Concept Logo, 8Knot Logo Color Variant on Olive Green Background, 8Knot Logo Vertical Black on White

### Community 25 - "Module Init Files"
Cohesion: 0.67
Nodes (1): Empty file that lets us import this folder as a module.

### Community 29 - "Search Type Detection"
Cohesion: 1.0
Nodes (1): Determine type of search item based on its identifying value

### Community 30 - "Nav Collapse Callback"
Cohesion: 1.0
Nodes (1): This dynamic callback manages the state of all collapsible nav items         by

### Community 86 - "Pages Overview Docs"
Cohesion: 1.0
Nodes (1): Pages Folder README

## Ambiguous Edges - Review These
- `Toolbar Chart - Bar Chart with Plotly Toolbar Controls` → `Right Arrow Icon - Navigation UI Element`  [AMBIGUOUS]
  8Knot/assets/rightarrow.png · relation: conceptually_related_to
- `Robot Head Icon - AI or Machine Learning Concept Logo` → `8Knot Brand / Application Identity`  [AMBIGUOUS]
  8Knot/assets/logo2.png · relation: conceptually_related_to

## Knowledge Gaps
- **117 isolated node(s):** `Configures Dash (Flask) server- makes login routes available.     Args:`, `(Worker Query)     Executes SQL query against Augur database for package depende`, `(Worker Query)     Executes SQL query against Augur database to get contributors`, `(Worker Query)     Executes SQL query against Augur database for contributor dat`, `(Worker Query)     Executes SQL query against Augur database for repo release in` (+112 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Module Init Files`** (3 nodes): `__init__.py`, `Empty file that lets us import this folder as a module.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Search Type Detection`** (1 nodes): `Determine type of search item based on its identifying value`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Nav Collapse Callback`** (1 nodes): `This dynamic callback manages the state of all collapsible nav items         by`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pages Overview Docs`** (1 nodes): `Pages Folder README`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Toolbar Chart - Bar Chart with Plotly Toolbar Controls` and `Right Arrow Icon - Navigation UI Element`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Robot Head Icon - AI or Machine Learning Concept Logo` and `8Knot Brand / Application Identity`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `get_uncached()` connect `Code Visualization & Heatmaps` to `Data Queries & Cache Layer`, `Search & State Management`, `Contributions & Issue Tracking`, `Contributor Behavior Analytics`, `Organization Affiliation Analysis`, `Repository Overview`, `Contributor Type Classification`, `CHAOSS Metrics`, `PR First Response Metrics`, `PR Review Response Metrics`, `Issue Assignment Metrics`?**
  _High betweenness centrality (0.259) - this node is a cross-community bridge._
- **Why does `AugurManager` connect `Core Application & Entry Points` to `Code Visualization & Heatmaps`, `Data Queries & Cache Layer`, `Search & State Management`, `Authentication & User Groups`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `caching_wrapper()` connect `Data Queries & Cache Layer` to `Code Visualization & Heatmaps`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 45 inferred relationships involving `AugurManager` (e.g. with `Testing utilities for 8Knot application.  This module provides utilities to inst` and `Configure logging to be more descriptive during testing.`) actually correct?**
  _`AugurManager` has 45 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `get_uncached()` (e.g. with `pr_first_response_graph()` and `cntrib_issue_assignment_graph()`) actually correct?**
  _`get_uncached()` has 40 INFERRED edges - model-reasoned connections that need verification._
