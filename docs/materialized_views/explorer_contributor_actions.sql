/* This is the SQL query that populates the explorer_contributor_actions materialized view*/

SELECT a.id AS cntrb_id,
    a.created_at,
    a.repo_id,
    a.action,
    repo.repo_name,
    a.login,
    row_number() OVER (PARTITION BY a.id, a.repo_id ORDER BY a.created_at DESC) AS rank
    FROM ( SELECT commits.cmt_ght_author_id AS id,
            commits.cmt_author_timestamp AS created_at,
            commits.repo_id,
            'commit'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.commits
             LEFT JOIN augur_data.contributors ON (((contributors.cntrb_id)::text = (commits.cmt_ght_author_id)::text)))
          GROUP BY commits.cmt_commit_hash, commits.cmt_ght_author_id, commits.repo_id, commits.cmt_author_timestamp, 'commit'::text, contributors.cntrb_login
        UNION ALL
         SELECT issues.reporter_id AS id,
            issues.created_at,
            issues.repo_id,
            'issue_opened'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.issues
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issues.reporter_id)))
          WHERE (issues.pull_request IS NULL)
        UNION ALL
         SELECT pull_request_events.cntrb_id AS id,
            pull_request_events.created_at,
            pull_requests.repo_id,
            'pull_request_closed'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_events.cntrb_id)))
          WHERE ((pull_requests.pull_request_id = pull_request_events.pull_request_id) AND (pull_requests.pr_merged_at IS NULL) AND ((pull_request_events.action)::text = 'closed'::text))
        UNION ALL
         SELECT pull_request_events.cntrb_id AS id,
            pull_request_events.created_at,
            pull_requests.repo_id,
            'pull_request_merged'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_events.cntrb_id)))
          WHERE ((pull_requests.pull_request_id = pull_request_events.pull_request_id) AND ((pull_request_events.action)::text = 'merged'::text))
        UNION ALL
         SELECT issue_events.cntrb_id AS id,
            issue_events.created_at,
            issues.repo_id,
            'issue_closed'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.issues,
            (augur_data.issue_events
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = issue_events.cntrb_id)))
          WHERE ((issues.issue_id = issue_events.issue_id) AND (issues.pull_request IS NULL) AND ((issue_events.action)::text = 'closed'::text))
        UNION ALL
         SELECT pull_request_reviews.cntrb_id AS id,
            pull_request_reviews.pr_review_submitted_at AS created_at,
            pull_requests.repo_id,
            ('pull_request_review_'::text || (pull_request_reviews.pr_review_state)::text) AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            (augur_data.pull_request_reviews
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = pull_request_reviews.cntrb_id)))
          WHERE (pull_requests.pull_request_id = pull_request_reviews.pull_request_id)
        UNION ALL
         SELECT pull_requests.pr_augur_contributor_id AS id,
            pull_requests.pr_created_at AS created_at,
            pull_requests.repo_id,
            'pull_request_open'::text AS action,
            contributors.cntrb_login AS login
           FROM (augur_data.pull_requests
             LEFT JOIN augur_data.contributors ON ((pull_requests.pr_augur_contributor_id = contributors.cntrb_id)))
        UNION ALL
         SELECT message.cntrb_id AS id,
            message.msg_timestamp AS created_at,
            pull_requests.repo_id,
            'pull_request_comment'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.pull_requests,
            augur_data.pull_request_message_ref,
            (augur_data.message
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
          WHERE ((pull_request_message_ref.pull_request_id = pull_requests.pull_request_id) AND (pull_request_message_ref.msg_id = message.msg_id))
        UNION ALL
         SELECT issues.reporter_id AS id,
            message.msg_timestamp AS created_at,
            issues.repo_id,
            'issue_comment'::text AS action,
            contributors.cntrb_login AS login
           FROM augur_data.issues,
            augur_data.issue_message_ref,
            (augur_data.message
             LEFT JOIN augur_data.contributors ON ((contributors.cntrb_id = message.cntrb_id)))
          WHERE ((issue_message_ref.msg_id = message.msg_id) AND (issues.issue_id = issue_message_ref.issue_id) AND (issues.closed_at <> message.msg_timestamp))) a,
    augur_data.repo
  WHERE (a.repo_id = repo.repo_id)
  ORDER BY a.created_at DESC
