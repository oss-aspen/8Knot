"""
    Imports
"""
import pandas as pd 
import sqlalchemy as salc
import json

class AugurInterface:

    def __init__(self, config: str = None) -> None:
        self.config = config
        self.engine = None

    def get_engine(self):
        """
            Connects to Augur instance using supplied config 
            credentials and returns the database engine.
        """

        if self.config is None:
            print("No config given- cannot get engine.")
            return None

        with open(self.config) as config_file:
            config = json.load(config_file)

        database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

        dbschema='augur_data'
        engine = salc.create_engine(
            database_connection_string,
            connect_args={'options': '-csearch_path={}'.format(dbschema)})

        self.engine = engine

        return engine

    def repo_name_to_id(self, repo_name: str) -> int:
        """
            Queries the Augur DB with the target name of a repository
            and returns the numerical ID of that repo if possible.
        """

        if self.engine is None:
            print("No engine- please use 'get_engine' method to create engine.")
            return None

        repo_query = salc.sql.text(f"""
                    SET SCHEMA 'augur_data';
                    SELECT 
                    b.repo_id
                FROM
                    repo_groups a,
                    repo b
                WHERE
                    a.repo_group_id = b.repo_group_id AND
                    b.repo_name = \'{repo_name}\'
        """)

        t = self.engine.execute(repo_query)
        repo_id: int =  t.mappings().all()[0].get('repo_id')
        return repo_id

    def run_query(self, query_string: str) -> pd.DataFrame:
        if self.engine is None:
            print("No engine- please use 'get_engine' method to create engine.")
            return None
        
        this_df = pd.DataFrame()

        # pr_query = salc.sql.text(f"""
        #             SELECT
        #                 r.repo_name,
        #                 c.cmt_commit_hash AS commits,
        #                 c.cmt_id AS file, 
        #                 c.cmt_added AS lines_added,
        #                 c.cmt_removed AS lines_removed,
        #                 c.cmt_author_date AS date
        #             FROM
        #                 repo r,
        #                 commits c
        #             WHERE
        #                 r.repo_id = c.repo_id AND
        #                 c.repo_id = \'{repo_id}\'
        #     """)

        pr_query = salc.sql.test(query_string)

        this_df = pd.read_sql(pr_query, con=self.engine)

        this_df = this_df.reset_index()
        this_df.drop("index", axis=1, inplace=True)

        return this_df