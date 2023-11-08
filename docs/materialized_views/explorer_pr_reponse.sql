/* This is the SQL query that populates the explorer_pr_assignments materialized view*/

SELECT
    pr.pull_request_id,
    pr.repo_id AS ID,
    pr.pr_augur_contributor_id AS cntrb_id,
    M.msg_timestamp,
    M.msg_cntrb_id,
    pr.pr_created_at,
    pr.pr_closed_at
FROM
    pull_requests pr
LEFT OUTER JOIN
    (
        SELECT
            prr.pull_request_id AS pull_request_id,
            m.msg_timestamp AS msg_timestamp,
            m.cntrb_id AS msg_cntrb_id
        FROM
            pull_request_review_message_ref prrmr,
            pull_requests pr,
            message m,
            pull_request_reviews prr
        WHERE
            prrmr.pr_review_id = prr.pr_review_id AND
            prrmr.msg_id = m.msg_id AND
            prr.pull_request_id = pr.pull_request_id
        UNION ALL
        SELECT
            prmr.pull_request_id AS pull_request_id,
            m.msg_timestamp AS msg_timestamp,
            m.cntrb_id AS msg_cntrb_id
        FROM
            pull_request_message_ref prmr,
            pull_requests pr,
            message m
        WHERE
            prmr.pull_request_id = pr.pull_request_id AND
            prmr.msg_id = m.msg_id
    ) M
ON
    M.pull_request_id = pr.pull_request_id
