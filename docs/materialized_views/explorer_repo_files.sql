/* SQL for the repository-files cache materialized view. */
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
    )
