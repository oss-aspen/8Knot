"""
    Imports
"""
import pandas as pd
import numpy as np
import sqlalchemy as salc
import os
import logging
import sys
import requests


class AugurManager:
    """
    Handles connection and queries to Augur database.

    Attributes:
    -----------
        pconfig : bool
            Flag of whether pconfig list was used to load current config.

        engine : _engine.Engine instance
            SQLAlchemy engine with credentials to connect to Augur database.

        user : str
            User credential to Augur database.

        password: str
            Password credential to Augur database.

        host : str
            Host credential to Augur database.

        port : str
            Port credential to Augur database.
            Which port on the server machine we'll target.

        database : str
            Database credential to Augur database.
            Which of the available databases on the server machine we'll target.

        schema : str
            Schema credential to Augur database.
            The target schema of the database we want to access.

        config_loaded : bool
            Flag of whether configuration params for database have been loaded.

    Methods:
    --------
        get_engine():
            Connects to Augur databse with supplied credentials and
            returns engine object.

        run_query(query_string):
            Runs a SQL-query against Augur database and returns resulting
            Pandas dataframe.

        package_pconfig():
            Packages current credentials into a list for transportation to workers.
            We need to do this because _engine.Engine objects can't be pickled and
            passed as parameters to workers via Queue objects.

        load_pconfig():
            Loads credentials for AugurManager object from a pconfig.
            We need to do this because _engine.Engine objects can't be pickled and
            passed as parameters to workers via Queue objects.
    """

    def __init__(self):
        self.pconfig = False
        self.client_secret = None
        self.session_generate_endpoint = None
        self.user_groups_endpoint = None
        self.engine = None
        self.user = None
        self.password = None
        self.host = None
        self.port = None
        self.database = None
        self.schema = None
        self.config_loaded = False
        self.entries = None
        self.all_entries = None
        self.search_input = None
        self.repo_dict = None
        self.org_dict = None
        self.app_id = None

    def get_engine(self):
        """
        Creates _engine.Engine object connected to our Augur database.

        Returns:
        --------
            _engine.Engine: SQLAlchemy engine object.
        """
        if self.engine is not None:
            return self.engine

        if self.config_loaded is False and not self.pconfig:

            # make sure all of the environment variables are available
            env_values = [
                "AUGUR_USERNAME",
                "AUGUR_PASSWORD",
                "AUGUR_HOST",
                "AUGUR_PORT",
                "AUGUR_DATABASE",
                "AUGUR_SCHEMA",
            ]
            for v in env_values:

                if v not in os.environ:
                    logging.critical(
                        f'Required environment variable "{v}" not available.'
                    )
                    return None

                if os.getenv(v) is None:
                    logging.critical(
                        f'Required environment variable: "{v}" available but none.'
                    )
                    return None

            # have confirmed that necessary environment variables exist- proceed.
            self.user = os.getenv("AUGUR_USERNAME")
            self.password = os.getenv("AUGUR_PASSWORD")
            self.host = os.getenv("AUGUR_HOST")
            self.port = os.getenv("AUGUR_PORT")
            self.database = os.getenv("AUGUR_DATABASE")
            self.schema = os.getenv("AUGUR_SCHEMA")
            self.config_loaded = True

        database_connection_string = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
            self.user, self.password, self.host, self.port, self.database
        )

        dbschema = self.schema
        try:
            engine = salc.create_engine(
                database_connection_string,
                connect_args={"options": "-csearch_path={}".format(dbschema)},
                pool_pre_ping=True,
            )
        except:
            logging.critical("Could not get engine- please check parameters.")

        self.engine = engine

        logging.debug("Engine returned")
        return engine

    def run_query(self, query_string: str) -> pd.DataFrame:
        """
        Runs SQL query against our Augur database.

        Args:
        -----
            query_string (str): SQL query to run.

        Returns:
        --------
            pd.DataFrame: Results from SQL query.
        """
        if self.engine is None:
            logging.critical(
                "No engine- please use 'get_engine' method to create engine."
            )
            return None

        result_df = pd.DataFrame()

        query = salc.sql.text(query_string)

        try:
            with self.engine.connect() as conn:
                result_df = pd.read_sql(query, con=conn)
        except:
            raise Exception("DB Read Failure")

        result_df = result_df.reset_index()
        result_df.drop("index", axis=1, inplace=True)

        return result_df

    def package_config(self):
        """
        Packages current credentials into a list for transportation to workers.
        We need to do this because _engine.Engine objects can't be pickled and
        passed as parameters to workers via Queue objects.

        Returns:
        --------
            list(str): List of credentials to recreate same connection to Augur instance.
        """
        if self.config_loaded:
            pconfig = [
                self.user,
                self.password,
                self.host,
                self.port,
                self.database,
                self.schema,
            ]
            return pconfig
        else:
            return None

    def load_pconfig(self, pconfig: list):
        """
        Loads credentials for AugurManager object from a pconfig.
        We need to do this because _engine.Engine objects can't be pickled and
        passed as parameters to workers via Queue objects.

        Args:
        -----
            pconfig (list): Credentials to create AugurManager object in RQ Workers.
        """
        self.pconfig = True
        self.engine = None
        self.user = pconfig[0]
        self.password = pconfig[1]
        self.host = pconfig[2]
        self.port = pconfig[3]
        self.database = pconfig[4]
        self.schema = pconfig[5]
        self.config_loaded = False
        self.get_engine()

    def project_list_query(self):

        pr_query = f"""SELECT DISTINCT
                            r.repo_git,
                            r.repo_id,
                            r.repo_name,
                            rg.rg_name
                        FROM
                            repo r
                        JOIN repo_groups rg
                        ON rg.repo_group_id = r.repo_group_id
                        ORDER BY rg.rg_name"""

        # query for search bar entry generation
        df_search_bar = self.run_query(pr_query)

        # handling case sensitive options for search bar
        self.entries = np.concatenate(
            (df_search_bar.rg_name.unique(), df_search_bar.repo_git.unique()), axis=None
        )
        self.entries = self.entries.tolist()
        self.entries.sort(key=lambda item: (item, len(item)))

        # generating search bar entries
        lower_entries = [i.lower() for i in self.entries]
        self.all_entries = list(zip(lower_entries, self.entries))

        # generating dictionary with the git urls as the key and the repo_id and name as a list as the value pair
        self.repo_dict = (
            df_search_bar[["repo_git", "repo_id", "repo_name"]]
            .set_index("repo_git")
            .T.to_dict("list")
        )

        # generating dictionary with the org name as the key and the git repos of the org in a list as the value pair
        self.org_dict = (
            df_search_bar.groupby("rg_name")["repo_git"].apply(list).to_dict()
        )

        # making first selection for the search bar
        self.search_input = self.entries[0]

    def get_search_input(self):
        if self.search_input is not None:
            return self.search_input
        else:
            r = self.project_list_query()
            return self.search_input

    def get_all_entries(self):
        if self.all_entries is not None:
            return self.all_entries
        else:
            r = self.project_list_query()
            return self.all_entries

    def get_org_dict(self):
        if self.org_dict is not None:
            return self.org_dict
        else:
            r = self.project_list_query()
            return self.org_dict

    def get_repo_dict(self):
        if self.repo_dict is not None:
            return self.repo_dict
        else:
            r = self.project_list_query()
            return self.repo_dict

    def auth_to_bearer_token(self, auth_token):
        """Large parts of code written by John McGinness, University of Missouri

        Returns:
            _type_: _description_
        """

        auth_params = {"code": auth_token, "grant_type": "code"}

        response = self.make_authenticated_request(params=auth_params)

        if response.status_code == 200:
            data = response.json()
            logging.critical(f"bearer token request payload: {data}")
            if data.get("status") == "Validated":
                return data["username"], data["access_token"], data["expires"], data["refresh_token"]
            else:
                return None, None, None, None
        else:
            return None, None, None, None

    def make_authenticated_request(self, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}"

        return requests.post(
            self.session_generate_endpoint, headers=headers, params=params
        )

    def make_user_request(self, access_token, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}, Bearer {access_token}"

        result = requests.post(
            self.user_groups_endpoint, headers=headers, params=params
        )

        if result.status_code == 200:
            return result.json()

    def set_client_secret(self, secret):
        self.client_secret = secret

    def set_session_generate_endpoint(self, endpoint):
        self.session_generate_endpoint = endpoint

    def set_user_groups_endpoint(self, endpoint):
        self.user_groups_endpoint = endpoint

    def set_app_id(self, id):
        self.app_id = id
