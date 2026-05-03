SET search_path TO augur_data;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_contributor_actions AS
SELECT a.id AS cntrb_id,
    a.created_at,
    a.repo_id,
    a.action,
    repo.repo_name,
    a.login,
    row_number() OVER (PARTITION BY a.id, a.repo_id ORDER BY a.created_at DESC) AS rank
FROM (
    SELECT commits.cmt_ght_author_id AS id,
        commits.cmt_author_timestamp AS created_at,
        commits.repo_id,
        'commit'::text AS action,
        contributors.cntrb_login AS login
    FROM commits
        LEFT JOIN contributors ON ((contributors.cntrb_id)::text = (commits.cmt_ght_author_id)::text)
    GROUP BY commits.cmt_commit_hash, commits.cmt_ght_author_id, commits.repo_id, commits.cmt_author_timestamp, 'commit'::text, contributors.cntrb_login
    UNION ALL
    SELECT issues.reporter_id AS id,
        issues.created_at,
        issues.repo_id,
        'issue_opened'::text AS action,
        contributors.cntrb_login AS login
    FROM issues
        LEFT JOIN contributors ON (contributors.cntrb_id = issues.reporter_id)
    WHERE (issues.pull_request IS NULL)
    UNION ALL
    SELECT pull_request_events.cntrb_id AS id,
        pull_request_events.created_at,
        pull_requests.repo_id,
        'pull_request_closed'::text AS action,
        contributors.cntrb_login AS login
    FROM pull_requests,
        (pull_request_events LEFT JOIN contributors ON (contributors.cntrb_id = pull_request_events.cntrb_id))
    WHERE (pull_requests.pull_request_id = pull_request_events.pull_request_id)
        AND (pull_requests.pr_merged_at IS NULL)
        AND (pull_request_events.action = 'closed')
    UNION ALL
    SELECT pull_request_events.cntrb_id AS id,
        pull_request_events.created_at,
        pull_requests.repo_id,
        'pull_request_merged'::text AS action,
        contributors.cntrb_login AS login
    FROM pull_requests,
        (pull_request_events LEFT JOIN contributors ON (contributors.cntrb_id = pull_request_events.cntrb_id))
    WHERE (pull_requests.pull_request_id = pull_request_events.pull_request_id)
        AND (pull_request_events.action = 'merged')
    UNION ALL
    SELECT issue_events.cntrb_id AS id,
        issue_events.created_at,
        issues.repo_id,
        'issue_closed'::text AS action,
        contributors.cntrb_login AS login
    FROM issues,
        (issue_events LEFT JOIN contributors ON (contributors.cntrb_id = issue_events.cntrb_id))
    WHERE (issues.issue_id = issue_events.issue_id)
        AND (issues.pull_request IS NULL)
        AND (issue_events.action = 'closed')
    UNION ALL
    SELECT pull_request_reviews.cntrb_id AS id,
        pull_request_reviews.pr_review_submitted_at AS created_at,
        pull_requests.repo_id,
        ('pull_request_review_' || pull_request_reviews.pr_review_state) AS action,
        contributors.cntrb_login AS login
    FROM pull_requests,
        (pull_request_reviews LEFT JOIN contributors ON (contributors.cntrb_id = pull_request_reviews.cntrb_id))
    WHERE (pull_requests.pull_request_id = pull_request_reviews.pull_request_id)
    UNION ALL
    SELECT pull_requests.pr_augur_contributor_id AS id,
        pull_requests.pr_created_at AS created_at,
        pull_requests.repo_id,
        'pull_request_open'::text AS action,
        contributors.cntrb_login AS login
    FROM pull_requests
        LEFT JOIN contributors ON (pull_requests.pr_augur_contributor_id = contributors.cntrb_id)
    UNION ALL
    SELECT message.cntrb_id AS id,
        message.msg_timestamp AS created_at,
        pull_requests.repo_id,
        'pull_request_comment'::text AS action,
        contributors.cntrb_login AS login
    FROM pull_requests,
        pull_request_message_ref,
        (message LEFT JOIN contributors ON (contributors.cntrb_id = message.cntrb_id))
    WHERE (pull_request_message_ref.pull_request_id = pull_requests.pull_request_id)
        AND (pull_request_message_ref.msg_id = message.msg_id)
    UNION ALL
    SELECT message.cntrb_id AS id,
        message.msg_timestamp AS created_at,
        issues.repo_id,
        'issue_comment'::text AS action,
        contributors.cntrb_login AS login
    FROM issues,
        issue_message_ref,
        (message LEFT JOIN contributors ON (contributors.cntrb_id = message.cntrb_id))
    WHERE (issue_message_ref.msg_id = message.msg_id)
        AND (issues.issue_id = issue_message_ref.issue_id)
        AND (issues.closed_at <> message.msg_timestamp)
) a,
repo
WHERE (a.repo_id = repo.repo_id)
ORDER BY a.created_at DESC
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_pr_response AS
SELECT
    pr.pull_request_id,
    pr.repo_id AS id,
    pr.pr_augur_contributor_id AS cntrb_id,
    m.msg_timestamp,
    m.cntrb_id AS msg_cntrb_id,
    pr.pr_created_at,
    pr.pr_closed_at
FROM pull_requests pr
LEFT OUTER JOIN (
    SELECT prr.pull_request_id,
        msg.msg_timestamp,
        msg.cntrb_id AS msg_cntrb_id
    FROM pull_request_review_message_ref prrmr,
        pull_requests pr2,
        message msg,
        pull_request_reviews prr
    WHERE prrmr.pr_review_id = prr.pr_review_id
        AND prrmr.msg_id = msg.msg_id
        AND prr.pull_request_id = pr2.pull_request_id
    UNION ALL
    SELECT prmr.pull_request_id,
        msg.msg_timestamp,
        msg.cntrb_id AS msg_cntrb_id
    FROM pull_request_message_ref prmr,
        pull_requests pr2,
        message msg
    WHERE prmr.pull_request_id = pr2.pull_request_id
        AND prmr.msg_id = msg.msg_id
) m ON m.pull_request_id = pr.pull_request_id
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_pr_files AS
SELECT
    prf.pr_file_path AS file_path,
    pr.pull_request_id,
    pr.repo_id
FROM pull_requests pr
INNER JOIN pull_request_files prf ON pr.pull_request_id = prf.pull_request_id
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_cntrb_per_file AS
SELECT
    pr.repo_id,
    prf.pr_file_path AS file_path,
    string_agg(DISTINCT CAST(pr.pr_augur_contributor_id AS varchar(15)), ',') AS cntrb_ids,
    string_agg(DISTINCT CAST(prr.cntrb_id AS varchar(15)), ',') AS reviewer_ids
FROM pull_requests pr
INNER JOIN pull_request_files prf ON pr.pull_request_id = prf.pull_request_id
LEFT OUTER JOIN pull_request_reviews prr ON pr.pull_request_id = prr.pull_request_id
GROUP BY prf.pr_file_path, pr.repo_id
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_pr_assignments AS
SELECT
    pr.pull_request_id,
    pr.repo_id AS id,
    pr.pr_created_at AS created,
    pr.pr_closed_at AS closed,
    pre.created_at AS assign_date,
    pre.action AS assignment_action,
    pre.cntrb_id AS assignee
FROM pull_requests pr
LEFT OUTER JOIN pull_request_events pre
    ON pr.pull_request_id = pre.pull_request_id
    AND pre.action IN ('unassigned', 'assigned')
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_issue_assignments AS
SELECT
    i.issue_id,
    i.repo_id AS id,
    i.created_at AS created,
    i.closed_at AS closed,
    ie.created_at AS assign_date,
    ie.action AS assignment_action,
    ie.cntrb_id AS assignee
FROM issues i
LEFT OUTER JOIN issue_events ie
    ON i.issue_id = ie.issue_id
    AND ie.action IN ('unassigned', 'assigned')
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_repo_languages AS
SELECT
    e.repo_id,
    r.repo_git,
    r.repo_name,
    e.programming_language,
    e.code_lines,
    e.files
FROM repo r,
(
    SELECT d.repo_id, d.programming_language,
        SUM(d.code_lines) AS code_lines,
        COUNT(*)::int AS files
    FROM (
        SELECT rl.repo_id, rl.programming_language, rl.code_lines
        FROM repo_labor rl,
        (
            SELECT rl2.repo_id, MAX(rl2.data_collection_date) AS last_collected
            FROM repo_labor rl2
            GROUP BY rl2.repo_id
        ) recent
        WHERE rl.repo_id = recent.repo_id
            AND rl.data_collection_date > recent.last_collected - (5 * interval '1 minute')
    ) d
    GROUP BY d.repo_id, d.programming_language
) e
WHERE r.repo_id = e.repo_id
ORDER BY e.repo_id
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS explorer_repo_files AS
SELECT
    rl.repo_id AS id,
    r.repo_name,
    r.repo_path,
    rl.rl_analysis_date,
    rl.file_path,
    rl.file_name
FROM repo_labor rl
INNER JOIN repo r ON rl.repo_id = r.repo_id
WHERE (rl.repo_id, rl.rl_analysis_date) IN (
    SELECT DISTINCT ON (repo_id) repo_id, rl_analysis_date
    FROM repo_labor
    ORDER BY repo_id, rl_analysis_date DESC
)
WITH NO DATA;
