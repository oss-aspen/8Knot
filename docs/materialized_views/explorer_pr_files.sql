/* This is the SQL query that populates the explorer_pr_files materialized view*/
SELECT
    prf.pr_file_path as file_path,
    pr.pull_request_id AS pull_request_id,
    pr.repo_id as repo_id
FROM
    pull_requests pr
INNER JOIN
    pull_request_files prf
ON
    pr.pull_request_id = prf.pull_request_id
