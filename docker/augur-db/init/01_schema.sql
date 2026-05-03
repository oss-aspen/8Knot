CREATE SCHEMA IF NOT EXISTS augur_data;

SET search_path TO augur_data;

CREATE TABLE IF NOT EXISTS repo_groups (
    repo_group_id BIGINT PRIMARY KEY,
    rg_name       VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS repo (
    repo_id       BIGINT PRIMARY KEY,
    repo_group_id BIGINT,
    repo_git      VARCHAR(1000),
    repo_path     VARCHAR(1000),
    repo_name     VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS contributors (
    cntrb_id        UUID PRIMARY KEY,
    cntrb_login     VARCHAR(255),
    cntrb_company   VARCHAR(255),
    cntrb_email     VARCHAR(255),
    cntrb_canonical VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS contributors_aliases (
    cntrb_alias_id BIGSERIAL PRIMARY KEY,
    cntrb_id       UUID,
    alias_email    VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS repo_info (
    repo_info_id          BIGSERIAL PRIMARY KEY,
    repo_id               BIGINT,
    issues_enabled        VARCHAR(10),
    fork_count            BIGINT,
    watchers_count        BIGINT,
    license               VARCHAR(255),
    stars_count           BIGINT,
    code_of_conduct_file  TEXT,
    security_issue_file   TEXT,
    security_audit_file   TEXT,
    data_collection_date  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS releases (
    release_id           BIGINT PRIMARY KEY,
    repo_id              BIGINT,
    release_name         VARCHAR(255),
    release_created_at   TIMESTAMP,
    release_published_at TIMESTAMP,
    release_updated_at   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repo_deps_scorecard (
    repo_deps_scorecard_id BIGSERIAL PRIMARY KEY,
    repo_id                BIGINT,
    name                   VARCHAR(500),
    score                  NUMERIC,
    data_collection_date   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repo_deps_libyear (
    repo_deps_libyear_id BIGSERIAL PRIMARY KEY,
    repo_id              BIGINT,
    name                 VARCHAR(500),
    current_release_date TIMESTAMP,
    latest_release_date  TIMESTAMP,
    libyear              NUMERIC,
    data_collection_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repo_labor (
    repo_labor_id        BIGSERIAL PRIMARY KEY,
    repo_id              BIGINT,
    rl_analysis_date     TIMESTAMP,
    data_collection_date TIMESTAMP,
    programming_language VARCHAR(255),
    code_lines           INTEGER,
    file_path            VARCHAR(1000),
    file_name            VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS commits (
    cmt_id                BIGSERIAL PRIMARY KEY,
    repo_id               BIGINT,
    cmt_commit_hash       VARCHAR(255),
    cmt_author_email      VARCHAR(255),
    cmt_author_date       VARCHAR(255),
    cmt_author_timestamp  TIMESTAMP,
    cmt_committer_timestamp TIMESTAMP,
    cmt_ght_author_id     UUID
);

CREATE TABLE IF NOT EXISTS issues (
    issue_id         BIGINT PRIMARY KEY,
    repo_id          BIGINT,
    gh_issue_number  BIGINT,
    gh_issue_id      BIGINT,
    reporter_id      UUID,
    cntrb_id         UUID,
    created_at       TIMESTAMP,
    closed_at        TIMESTAMP,
    pull_request_id  BIGINT,
    pull_request     BIGINT
);

CREATE TABLE IF NOT EXISTS pull_requests (
    pull_request_id          BIGINT PRIMARY KEY,
    repo_id                  BIGINT,
    pr_src_number            BIGINT,
    pr_augur_contributor_id  UUID,
    pr_created_at            TIMESTAMP,
    pr_closed_at             TIMESTAMP,
    pr_merged_at             TIMESTAMP
);

CREATE TABLE IF NOT EXISTS message (
    msg_id        BIGINT PRIMARY KEY,
    msg_timestamp TIMESTAMP,
    cntrb_id      UUID
);

CREATE TABLE IF NOT EXISTS pull_request_files (
    pr_file_id      BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT,
    pr_file_path    VARCHAR(1000)
);

CREATE TABLE IF NOT EXISTS pull_request_events (
    pr_event_id     BIGINT PRIMARY KEY,
    pull_request_id BIGINT,
    created_at      TIMESTAMP,
    action          VARCHAR(255),
    cntrb_id        UUID
);

CREATE TABLE IF NOT EXISTS pull_request_reviews (
    pr_review_id          BIGINT PRIMARY KEY,
    pull_request_id       BIGINT,
    cntrb_id              UUID,
    pr_review_submitted_at TIMESTAMP,
    pr_review_state       VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS pull_request_message_ref (
    pr_msgref_id    BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT,
    msg_id          BIGINT
);

CREATE TABLE IF NOT EXISTS pull_request_review_message_ref (
    pr_review_msgref_id BIGSERIAL PRIMARY KEY,
    pr_review_id        BIGINT,
    msg_id              BIGINT
);

CREATE TABLE IF NOT EXISTS issue_events (
    issue_event_id BIGINT PRIMARY KEY,
    issue_id       BIGINT,
    created_at     TIMESTAMP,
    action         VARCHAR(255),
    cntrb_id       UUID
);

CREATE TABLE IF NOT EXISTS issue_message_ref (
    issue_msgref_id BIGSERIAL PRIMARY KEY,
    issue_id        BIGINT,
    msg_id          BIGINT
);
