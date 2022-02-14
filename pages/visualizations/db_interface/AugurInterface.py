"""
    Imports
"""
import pandas as pd 
import sqlalchemy as salc
import json
import os

class AugurInterface:

    def __init__(self, config: str = None) -> None:
        self.config = config
        self.engine = None
        self.user = None
        self.password = None
        self.host = None 
        self.port = None
        self.database = None
        self.schema = None
        self.config_loaded = False

    def get_engine(self):
        """
            Connects to Augur instance using supplied config 
            credentials and returns the database engine.
        """

        """
            If we have been passed a config file, try to read it.
        """
        if self.config is not None:
            print("Attempting to load parameters from config.")
            try:
                with open(self.config) as config_file:
                    config = json.load(config_file)
                    
                    self.user = config['user']
                    self.password = config['password']
                    self.host = config['host']
                    self.port = config['port']
                    self.database = config['database']
                    self.schema = config['schema']
                    self.config_loaded = True

            except FileNotFoundError:
                print("No config file exists of passed name.")
                print("Defaulting to environment variables.")
            except KeyError:
                print("One or more of the needed config parameters were not in the config.")
                print("Defaulting to environment variables.")

        if self.config_loaded is False:
            """
                Try to get the db_connection_string parameters
                from the environment variables where the program is running.

                We try to do this if there is no config available or if loading necessary parameters
                from the passed config file is not possible.
            """

            print("Attempting to load parameters from environment.")
            try:
                self.user = os.environ['user']
                self.password = os.environ['password']
                self.host = os.environ['host']
                self.port = os.environ['port']
                self.database = os.environ['database']
                self.schema = os.environ['schema']
            except KeyError:
                print("Make sure all environment variables needed to connect to database are set.")
                return

        database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(self.user, self.password, self.host, self.port, self.database)

        dbschema=self.schema
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

        pr_query = salc.sql.text(query_string)

        this_df = pd.read_sql(pr_query, con=self.engine)

        this_df = this_df.reset_index()
        this_df.drop("index", axis=1, inplace=True)

        return this_df