-- Script to create materialized views for 8Knot heatmap functionality
-- Run this against your Augur database before testing

-- 1. Create explorer_repo_files materialized view
DROP MATERIALIZED VIEW IF EXISTS augur_data.explorer_repo_files CASCADE;
CREATE MATERIALIZED VIEW augur_data.explorer_repo_files AS
SELECT
    rl.repo_id AS repo_id,
    r.repo_name,
    r.repo_path,
    rl.rl_analysis_date,
    rl.file_path,
    rl.file_name
FROM
    augur_data.repo_labor rl
INNER JOIN
    augur_data.repo r
ON
    rl.repo_id = r.repo_id
WHERE
    (rl.repo_id, rl.rl_analysis_date) IN (
        SELECT DISTINCT ON (repo_id)
            repo_id, rl_analysis_date
        FROM augur_data.repo_labor
        ORDER BY repo_id, rl_analysis_date DESC
    );

-- Create index for performance
CREATE INDEX idx_explorer_repo_files_repo_id ON augur_data.explorer_repo_files(repo_id);

-- 2. Create explorer_cntrb_per_file materialized view
DROP MATERIALIZED VIEW IF EXISTS augur_data.explorer_cntrb_per_file CASCADE;
CREATE MATERIALIZED VIEW augur_data.explorer_cntrb_per_file AS
SELECT
    pr.repo_id as repo_id,
    prf.pr_file_path as file_path,
    string_agg(DISTINCT CAST(pr.pr_augur_contributor_id AS varchar(15)), ',') AS cntrb_ids,
    string_agg(DISTINCT CAST(prr.cntrb_id AS varchar(15)), ',') AS reviewer_ids
FROM
    augur_data.pull_requests pr
INNER JOIN
    augur_data.pull_request_files prf
ON
    pr.pull_request_id = prf.pull_request_id
LEFT OUTER JOIN
    augur_data.pull_request_reviews prr
ON
    pr.pull_request_id = prr.pull_request_id
GROUP BY prf.pr_file_path, pr.repo_id;

-- Create index for performance
CREATE INDEX idx_explorer_cntrb_per_file_repo_id ON augur_data.explorer_cntrb_per_file(repo_id);

-- 3. Create explorer_pr_files materialized view
DROP MATERIALIZED VIEW IF EXISTS augur_data.explorer_pr_files CASCADE;
CREATE MATERIALIZED VIEW augur_data.explorer_pr_files AS
SELECT
    prf.pr_file_path as file_path,
    pr.pull_request_id AS pull_request_id,
    pr.repo_id as repo_id
FROM
    augur_data.pull_requests pr
INNER JOIN
    augur_data.pull_request_files prf
ON
    pr.pull_request_id = prf.pull_request_id;

-- Create index for performance
CREATE INDEX idx_explorer_pr_files_repo_id ON augur_data.explorer_pr_files(repo_id);

-- Verify views were created
SELECT
    schemaname,
    matviewname,
    ispopulated
FROM pg_matviews
WHERE matviewname LIKE 'explorer_%'
ORDER BY matviewname;

-- Quick test queries (replace 25430 with a repo_id from your database)
-- SELECT COUNT(*) FROM augur_data.explorer_repo_files WHERE repo_id = 25430;
-- SELECT COUNT(*) FROM augur_data.explorer_cntrb_per_file WHERE repo_id = 25430;
-- SELECT COUNT(*) FROM augur_data.explorer_pr_files WHERE repo_id = 25430;
