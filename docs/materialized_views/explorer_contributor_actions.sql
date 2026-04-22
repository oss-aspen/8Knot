/* This is the SQL query that populates the explorer_contributor_actions materialized view*/

CREATE MATERIALIZED VIEW augur_data.explorer_contributor_actions AS
SELECT
    a.cntrb_id,
    a.created_at,
    a.repo_id,
    a.action,
    a.repo_name,
    co.cntrb_login AS login
FROM (
    -- issues opened
    SELECT
        i.reporter_id                  AS cntrb_id,
        i.created_at,
        i.repo_id,
        'issue_opened'::text           AS action,
        r.repo_name
    FROM augur_data.issues i
    JOIN augur_data.repo r ON r.repo_id = i.repo_id
    WHERE i.pull_request IS NULL

    UNION ALL

    -- pull requests closed (not merged)
    SELECT
        pre.cntrb_id,
        pre.created_at,
        pr.repo_id,
        'pull_request_closed'::text    AS action,
        r.repo_name
    FROM augur_data.pull_request_events pre
    JOIN augur_data.pull_requests pr
        ON pr.pull_request_id = pre.pull_request_id
        AND pr.pr_merged_at IS NULL
    JOIN augur_data.repo r ON r.repo_id = pr.repo_id
    WHERE pre.action = 'closed'

    UNION ALL

    -- pull requests merged
    SELECT
        pre.cntrb_id,
        pre.created_at,
        pr.repo_id,
        'pull_request_merged'::text    AS action,
        r.repo_name
    FROM augur_data.pull_request_events pre
    JOIN augur_data.pull_requests pr
        ON pr.pull_request_id = pre.pull_request_id
    JOIN augur_data.repo r ON r.repo_id = pr.repo_id
    WHERE pre.action = 'merged'

    UNION ALL

    -- issues closed
    SELECT
        ie.cntrb_id,
        ie.created_at,
        i.repo_id,
        'issue_closed'::text           AS action,
        r.repo_name
    FROM augur_data.issue_events ie
    JOIN augur_data.issues i
        ON i.issue_id = ie.issue_id
        AND i.pull_request IS NULL
    JOIN augur_data.repo r ON r.repo_id = i.repo_id
    WHERE ie.action = 'closed'

    UNION ALL

    -- pull request reviews
    SELECT
        prr.cntrb_id,
        prr.pr_review_submitted_at     AS created_at,
        pr.repo_id,
        ('pull_request_review_' || prr.pr_review_state::text) AS action,
        r.repo_name
    FROM augur_data.pull_request_reviews prr
    JOIN augur_data.pull_requests pr
        ON pr.pull_request_id = prr.pull_request_id
    JOIN augur_data.repo r ON r.repo_id = pr.repo_id

    UNION ALL

    -- pull requests opened
    SELECT
        pr.pr_augur_contributor_id     AS cntrb_id,
        pr.pr_created_at               AS created_at,
        pr.repo_id,
        'pull_request_open'::text      AS action,
        r.repo_name
    FROM augur_data.pull_requests pr
    JOIN augur_data.repo r ON r.repo_id = pr.repo_id

    UNION ALL

    -- pull request comments
    SELECT
        m.cntrb_id,
        m.msg_timestamp                AS created_at,
        pr.repo_id,
        'pull_request_comment'::text   AS action,
        r.repo_name
    FROM augur_data.pull_request_message_ref prmr
    JOIN augur_data.pull_requests pr
        ON pr.pull_request_id = prmr.pull_request_id
    JOIN augur_data.repo r ON r.repo_id = pr.repo_id
    JOIN augur_data.message m ON m.msg_id = prmr.msg_id

    UNION ALL

    -- issue comments
    SELECT
        m.cntrb_id,
        m.msg_timestamp                AS created_at,
        i.repo_id,
        'issue_comment'::text          AS action,
        r.repo_name
    FROM augur_data.issue_message_ref imr
    JOIN augur_data.message m ON m.msg_id = imr.msg_id
    JOIN augur_data.issues i
        ON i.issue_id = imr.issue_id
        AND i.pull_request IS NULL
        AND i.closed_at <> m.msg_timestamp
    JOIN augur_data.repo r ON r.repo_id = i.repo_id
) a
LEFT JOIN augur_data.contributors co ON co.cntrb_id = a.cntrb_id
ORDER BY a.created_at DESC;
