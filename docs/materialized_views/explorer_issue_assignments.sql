/* This is the SQL query that populates the explorer_issue_assignments materialized view*/

SELECT
    i.issue_id,
    i.repo_id AS id,
    i.created_at as created,
    i.closed_at as closed,
    ie.created_at AS assign_date,
    ie.action AS assignment_action,
    ie.cntrb_id AS assignee
FROM
    issues i
LEFT OUTER JOIN
    issue_events ie
ON
    i.issue_id = ie.issue_id AND
    ie.action IN ('unassigned', 'assigned')
