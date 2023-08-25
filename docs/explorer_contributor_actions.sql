/* This is the SQL query that populates the explorer_contributor_actions materialized view*/

SELECT
	A.ID AS cntrb_id,
	A.created_at,
	A.repo_id,
	A.ACTION,
	repo.repo_name,
	A.LOGIN,
	DENSE_RANK() OVER(PARTITION BY A.ID, A.repo_id ORDER BY A.created_at) AS RANK
FROM (
	select
		commits.cmt_ght_author_id AS ID,
		commits.cmt_author_timestamp AS created_at,
		commits.repo_id,
		'commit' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		( augur_data.commits LEFT JOIN augur_data.contributors ON ( ( ( contributors.cntrb_id ) :: TEXT = ( commits.cmt_ght_author_id ) :: TEXT ) ) )
	GROUP BY
		commits.cmt_commit_hash,
		commits.cmt_ght_author_id,
		commits.repo_id,
		commits.cmt_author_timestamp,
		'commit' :: TEXT,
		contributors.cntrb_login
	UNION all
	SELECT
		issues.reporter_id AS ID,
		issues.created_at,
		issues.repo_id,
		'issue_opened' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		( augur_data.issues LEFT JOIN augur_data.contributors ON ( ( contributors.cntrb_id = issues.reporter_id ) ) )
	WHERE
		( issues.pull_request IS NULL )
	UNION ALL
	SELECT
		pull_request_events.cntrb_id AS ID,
		pull_request_events.created_at,
		pull_requests.repo_id,
		'pull_request_closed' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		augur_data.pull_requests,
		( augur_data.pull_request_events LEFT JOIN augur_data.contributors ON ( ( contributors.cntrb_id = pull_request_events.cntrb_id ) ) )
	WHERE
		pull_requests.pull_request_id = pull_request_events.pull_request_id
		AND pull_requests.pr_merged_at IS NULL
		AND ( ( pull_request_events.ACTION ) :: TEXT = 'closed' :: TEXT )
	UNION ALL
	SELECT
		pull_request_events.cntrb_id AS ID,
		pull_request_events.created_at,
		pull_requests.repo_id,
		'pull_request_merged' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		augur_data.pull_requests,
		( augur_data.pull_request_events LEFT JOIN augur_data.contributors ON ( ( contributors.cntrb_id = pull_request_events.cntrb_id ) ) )
	WHERE
		pull_requests.pull_request_id = pull_request_events.pull_request_id
		AND ( ( pull_request_events.ACTION ) :: TEXT = 'merged' :: TEXT )
	UNION ALL
	SELECT
		issue_events.cntrb_id AS ID,
		issue_events.created_at,
		issues.repo_id,
		'issue_closed' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		augur_data.issues,
		augur_data.issue_events
		LEFT JOIN augur_data.contributors ON contributors.cntrb_id = issue_events.cntrb_id
	WHERE
		issues.issue_id = issue_events.issue_id
		AND issues.pull_request IS NULL
		AND ( ( issue_events.ACTION ) :: TEXT = 'closed' :: TEXT )
	UNION ALL
	SELECT
		pull_request_reviews.cntrb_id AS ID,
		pull_request_reviews.pr_review_submitted_at AS created_at,
		pull_requests.repo_id,
		( 'pull_request_review_' :: TEXT || ( pull_request_reviews.pr_review_state ) :: TEXT ) AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		augur_data.pull_requests,
		augur_data.pull_request_reviews
		LEFT JOIN augur_data.contributors ON contributors.cntrb_id = pull_request_reviews.cntrb_id
	WHERE
		pull_requests.pull_request_id = pull_request_reviews.pull_request_id
	UNION ALL
	SELECT
		pull_requests.pr_augur_contributor_id AS ID,
		pull_requests.pr_created_at AS created_at,
		pull_requests.repo_id,
		'pull_request_open' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		augur_data.pull_requests
		LEFT JOIN augur_data.contributors ON pull_requests.pr_augur_contributor_id = contributors.cntrb_id
	UNION ALL
	SELECT
		message.cntrb_id AS ID,
		message.msg_timestamp AS created_at,
		pull_requests.repo_id,
		'pull_request_comment' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		augur_data.pull_requests,
		augur_data.pull_request_message_ref,
		augur_data.message
		LEFT JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id
	WHERE
		pull_request_message_ref.pull_request_id = pull_requests.pull_request_id
		AND pull_request_message_ref.msg_id = message.msg_id
	UNION ALL
	SELECT
		issues.reporter_id AS ID,
		message.msg_timestamp AS created_at,
		issues.repo_id,
		'issue_comment' :: TEXT AS ACTION,
		contributors.cntrb_login AS LOGIN
	FROM
		augur_data.issues,
		augur_data.issue_message_ref,
		augur_data.message
		LEFT JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id
	WHERE
		issue_message_ref.msg_id = message.msg_id
		AND issues.issue_id = issue_message_ref.issue_id
		AND issues.closed_at != message.msg_timestamp
	) A,
	augur_data.repo
	WHERE
	A.repo_id = repo.repo_id
	ORDER BY
			A.created_at DESC
