"""
NOTES ABOUT THIS FILE:

This file uses raw SQL to create tables in Postgres.
It's typically easiest and best-practice to use a db migration
tool instead of doing error-prone manual administration like this.

However, using sqlalchemy and alembic (Python db migration stack)
would be a bit of a steep learning curve for people who just want to
create a table in the cache. Most people who would be working on a
project like this will know enough SQL to read the existing table
definitions and create a new table as needed from those examples.

Our data model is fairly simple, so for now the overhead of proper
db migration tooling is mostly bloaty. We can return to this decision
in the future if necessary.
"""

"""
TABLE_CREATION_INSTRUCTIONS:

For data that we retrieve from Postgres to be cached, we need
to define the "schema" for the table where it will be stored.

Take a moment to look at the correspondence between the table
"commits_query" in this file and the SQL that we have the database
execute, defined in "queries/commits_query.py." Notice that each
of the columns referenced in the SELECT statement has a
corresponding column in the table schema defined below, with a
type that matches the datatype we expect to receive from Augur.

Note also that we use the table creation syntax:
CREATE UNLOGGED TABLE IF NOT EXISTS <name>

We configure the tables to be unlogged to maximize write-to speed.
We can always repopulate a table with minimal inconvenience if
the cache database is destroyed, so we don't need the durability
guarantees of a logged table.

We also only create a new table if a table of the same name
does not already exist. This initialization script ALWAYS runs
on app startup to make sure that the schema of the databse is
intact between application restarts.

To add a new table to the cache, simply copy an existing table
creation block from those below. Given that you're creating a table
for a query in the 'queries/' folder, name the table the same name
as the query function. Name the columns of the table, and give their
types, and everything should work!

Here's a list of types that postgres defines:
https://www.postgresql.org/docs/current/datatype.html

Generally, 'int' is good for integers,
'float4' is good for normal floats,
'float8' is good for larger precision floats,
'text' is best for text strings.
    - why we aren't using 'varchar':
    https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_varchar.28n.29_by_default
"""

import logging
import sys
import psycopg2 as pg

# doesn't use relative import syntax "import .cx_common" because
# cx_common is a neighbor of script, thus is available in PYTHON_PATH
from cx_common import init_cx_string, cache_cx_string


def _create_application_database() -> None:
    """
    On fresh application boot, Postgres is fresh, so
    database where we cache data from Augur isn't configured.

    This function creates the 'augur_cache' database, which will
    contain all of the tables where we'll cache data for visualization.
    """

    # Connect to the dbms at top-level
    # to instantiate application db
    # we'll always connect to root-level DB
    # with these creds so they don't need to be
    # parameterized.
    conn = pg.connect(init_cx_string)

    # required so that we can create a database
    conn.autocommit = True

    # check if application db already exists
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'augur_cache'")
    exists = cur.fetchone()

    # create application db if it doesn't already exist
    if not exists:
        logging.warning("CREATING augur_cache DATABASE")
        cur.execute("CREATE DATABASE augur_cache")

    conn.commit()
    cur.close()
    conn.close()


def _create_application_tables() -> None:
    """
    Creates tables for cached data in 'augur_cache' database.

    Tables created:
        - commits
        - cache_bookkeeping
    """
    # TODO: timestamps being stored as strings- don't need to do that anymore.

    # connect to application database
    conn = pg.connect(cache_cx_string)

    with conn.cursor() as cur:
        # create tables if they don't already exist.
        # TODO: id->repo_id, commits->commit_id
        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS commits_query(
                repo_id int,
                commit_hash text, -- this is the commit hash, so it's base64 hash.
                author_email text,
                author_date text,
                author_timestamp text,
                committer_timestamp text)
            """
        )
        logging.warning("CREATED commits TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS issues_query(
                repo_id bigint,
                repo_name text,
                issue bigint,
                issue_number bigint,
                gh_issue bigint,
                reporter_id text,
                issue_closer text,
                created_at text,
                closed_at text
            )
            """
        )
        logging.warning("CREATED issues TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS prs_query(
                repo_id int,
                repo_name text,
                pull_request_id int,
                pr_src_number int,
                cntrb_id text,
                created_at text,
                closed_at text,
                merged_at text
            )
            """
        )
        logging.warning("CREATED prs TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS affiliation_query(
                cntrb_id text,
                created_at text,
                repo_id int,
                login text,
                action text,
                rank int,
                cntrb_company text,
                email_list text
            )
            """
        )
        logging.warning("CREATED affiliation_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS contributors_query(
                repo_id int,
                repo_name text,
                cntrb_id text,
                created_at text,
                login text,
                action text,
                rank int
            )
            """
        )
        logging.warning("CREATED contributors TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS issue_assignee_query(
                issue_id text,
                repo_id int,
                created_at text,
                closed_at text,
                assign_date text,
                assignment_action text,
                assignee text
            )
            """
        )
        logging.warning("CREATED issue_assignments TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS pr_assignee_query(
                pull_request_id int,
                repo_id int,
                created_at text,
                closed_at text,
                assign_date text,
                assignment_action text,
                assignee text
            )
            """
        )
        logging.warning("CREATED pr_assignments TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS cntrb_per_file_query(
                repo_id int,
                file_path text,
                cntrb_ids text,
                reviewer_ids text
            )
            """
        )
        logging.warning("CREATED cntrb_per_file_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS pr_file_query(
                file_path text,
                pull_request_id int,
                repo_id int
            )
            """
        )
        logging.warning("CREATED pr_file_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_files_query(
                repo_id int,
                repo_name text,
                repo_path text,
                rl_analysis_date text,
                file_path text,
                file_name text
            )
            """
        )
        logging.warning("CREATED repo_files_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_languages_query(
                repo_id int,
                programming_language text,
                code_lines int,
                files int
            )
            """
        )
        logging.warning("CREATED repo_languages_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS package_version_query(
                repo_id int,
                name text,
                current_release_date text,
                latest_release_date text,
                libyear float4,
                dep_age text
            )
            """
        )
        logging.warning("CREATED package_version_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_releases_query(
                repo_id int,
                release_name text,
                release_created_at text,
                release_published_at text,
                release_updated_at text
            )
            """
        )
        logging.warning("CREATED repo_releases_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS ossf_score_query(
                repo_id int,
                name text,
                score float4,
                data_collection_date timestamp
            )
            """
        )
        logging.warning("CREATED ossf_score_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS repo_info_query(
                repo_id int,
                issues_enabled text,
                fork_count int,
                watchers_count int,
                license text,
                stars_count int,
                code_of_conduct_file text,
                security_issue_file text,
                security_audit_file text,
                data_collection_date timestamp
            )
            """
        )
        logging.warning("CREATED repo_info_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS pr_response_query(
                pull_request_id int,
                repo_id int,
                cntrb_id text,
                msg_timestamp text,
                msg_cntrb_id text,
                pr_created_at text,
                pr_closed_at text
            )
            """
        )
        logging.warning("CREATED pr_response_query TABLE")

        cur.execute(
            """
            CREATE UNLOGGED TABLE IF NOT EXISTS cache_bookkeeping(
                cache_func text,
                repo_id int,
                ts_cached timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        logging.warning("CREATED cache_bookkeeping TABLE")

        # commit changes, all-or-nothing.
        conn.commit()

    logging.warning("ALL TABLES COMMITTED SUCCESSFULLY")


def db_init() -> int:
    try:
        # don't need to check return values- errors propogate as exceptions,
        # which will halt init altogether.

        # create augur_cache db if it doesn't already exist.
        _create_application_database()

        # add tables to augur_cache db if they don't already exist.
        _create_application_tables()

        logging.warning("db_init: POSTGRES CACHE SUCCESSFULLY INITIALIZED")

        return 0

    except Exception as e:
        logging.critical(f"POSTGRES ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(db_init())
