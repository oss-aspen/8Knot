SET search_path TO augur_data;

REFRESH MATERIALIZED VIEW explorer_contributor_actions;
REFRESH MATERIALIZED VIEW explorer_pr_response;
REFRESH MATERIALIZED VIEW explorer_pr_files;
REFRESH MATERIALIZED VIEW explorer_cntrb_per_file;
REFRESH MATERIALIZED VIEW explorer_pr_assignments;
REFRESH MATERIALIZED VIEW explorer_issue_assignments;
REFRESH MATERIALIZED VIEW explorer_repo_languages;
REFRESH MATERIALIZED VIEW explorer_repo_files;
