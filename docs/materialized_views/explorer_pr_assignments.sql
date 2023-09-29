/* This is the SQL query that populates the explorer_pr_assignments materialized view*/

SELECT
    pr.pull_request_id,
    pr.repo_id AS id,
    pr.pr_created_at AS created,
    pr.pr_closed_at as closed,
    pre.created_at AS assign_date,
    pre.action AS assignment_action,
    pre.cntrb_id AS assignee
FROM
    pull_requests pr
LEFT OUTER JOIN
    pull_request_events pre
ON
    pr.pull_request_id = pre.pull_request_id AND
    pre.action IN ('unassigned', 'assigned')
