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
import traceback
import time


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
        self.app_id = None
        self.user_account_endpoint = None
        self.user_auth_endpoint = None

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
                    logging.critical(f'Required environment variable "{v}" not available.')
                    return None

                if os.getenv(v) is None:
                    logging.critical(f'Required environment variable: "{v}" available but none.')
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
            logging.critical("No engine- please use 'get_engine' method to create engine.")
            return None

        result_df = pd.DataFrame()

        query = salc.sql.text(query_string)

        # try to connect to augur to run query 5 times
        # TODO: this is a terrible patch for the problem. Should be using
        # job retries with the task manager so that the problem is
        # scheduled. However, the problem occurs only 1/13 metrics only
        # sometimes so the more major fix will come later.
        for i in range(5):
            try:
                with self.engine.connect() as conn:
                    result_df = pd.read_sql(query, con=conn)
                    break
            except:
                if i < 4:
                    # give more time in between trials.
                    time.sleep((i + 1) * 2.0)
                else:
                    raise Exception("DB Read failed.")

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

    def multiselect_startup(self):

        logging.debug(f"MULTISELECT_STARTUP")

        query_string = f"""SELECT DISTINCT
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
        df_search_bar = self.run_query(query_string)
        logging.debug(f"MULTISELECT_QUERY")

        # create a list of dictionaries for the MultiSelect dropdown
        # component on the index page.
        # Output is of the form: [{"label": repo_url, "value": repo_id}, ...]
        multiselect_repos = (
            df_search_bar[["repo_git", "repo_id"]]
            .rename(columns={"repo_git": "label", "repo_id": "value"})
            .to_dict("records")
        )

        # create a list of dictionaries for the MultiSelect dropdown
        # Output is of the form: [{"label": org_name, "value": lower(org_name)}, ...]
        multiselect_orgs = [{"label": v, "value": str.lower(v)} for v in list(df_search_bar["rg_name"].unique())]

        # combine options for multiselect component and sort them by the length
        # of their label (shorter comes first because it sorts ascending by default.)
        self.multiselect_options = multiselect_repos + multiselect_orgs
        self.multiselect_options = sorted(self.multiselect_options, key=lambda i: i["label"])

        # create a dictionary to map github orgs to their constituent repos.
        # used when the user selects an org
        # Output is of the form: {group_name: [rid1, rid2, ...], group_name: [...], ...}
        df_lower_repo_names = df_search_bar.copy()
        df_lower_repo_names["rg_name"] = df_lower_repo_names["rg_name"].apply(str.lower)
        self.org_name_to_repos_dict = df_lower_repo_names.groupby("rg_name")["repo_id"].apply(list).to_dict()
        self.org_names = list(self.org_name_to_repos_dict.keys())

        # create a dictionary that maps the github url to the repo_id in database
        df_repo_git_id = df_search_bar.copy()
        df_repo_git_id = df_repo_git_id[["repo_git", "repo_id"]]
        self.repo_git_to_repo_id = pd.Series(df_repo_git_id.repo_id.values, index=df_repo_git_id["repo_git"]).to_dict()

        # making first selection for the search bar
        self.initial_search_option = self.multiselect_options[0]
        logging.debug(f"MULTISELECT_FINISHED")

    def repo_git_to_id(self, git):
        """Getter method for dictionary
        that converts a git URL to the respective
        repo_id in the source db.

        Args:
            git (str): URL of repo

        Returns:
            int: repo_id of the URL in the source DB.
        """
        return self.repo_git_to_repo_id.get(git)

    def org_to_repos(self, org):
        """Returns the list of repos in an org.

        Args:
            org (str): Github org name

        Returns:
            [int] | None: repo_ids or None
        """
        return self.org_name_to_repos_dict[org]

    def is_org(self, org):
        """Checks if org name in set of known org names

        Args:
            org (str): name of org

        Returns:
            bool: whether org name is in orgs
        """
        return org in self.org_names

    def initial_multiselect_option(self):
        """Getter method on first multiselect option

        Returns:
            dict(value, label): first thing the multiselect will represent on startup
        """
        return self.initial_search_option

    def get_multiselect_options(self):
        """Getter method on all entries in repo+orgs options
        for the multiselect dropdown.

        Returns:
            [{label, value}]: multiselect options
        """
        return self.multiselect_options

    def auth_to_bearer_token(self, auth_token):
        """Large parts of code written by John McGinness, University of Missouri

        Returns:
            _type_: _description_
        """

        auth_params = {"code": auth_token, "grant_type": "code"}

        response = self.make_authenticated_request(params=auth_params)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "Validated":
                return (
                    data["username"],
                    data["access_token"],
                    data["expires"],
                    data["refresh_token"],
                )
            else:
                logging.critical(f"AUGUR-MANAGER FAILURE: Couldn't get Bearer Token, response not Validated.")
                return None, None, None, None
        else:
            logging.critical(f"AUGUR-MANAGER FAILURE: Couldn't get Bearer Token, non-200 status.")
            return None, None, None, None

    def make_authenticated_request(self, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}"

        return requests.post(self.session_generate_endpoint, headers=headers, params=params)

    def make_user_request(self, access_token, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}, Bearer {access_token}"

        result = requests.post(self.user_groups_endpoint, headers=headers, params=params)

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

    def set_user_account_endpoint(self, endpoint):
        self.user_account_endpoint = endpoint

    def set_user_auth_endpoint(self, endpoint):
        self.user_auth_endpoint = endpoint
