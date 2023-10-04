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
from sqlalchemy.exc import SQLAlchemyError


class AugurManager:
    """
    Handles connection and queries to Augur database.

    Attributes:
    -----------
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

    Methods:
    --------
        get_engine():
            Connects to Augur databse with supplied credentials and
            returns engine object.

        run_query(query_string):
            Runs a SQL-query against Augur database and returns resulting
            Pandas dataframe.
    """

    def __init__(self, handles_oauth=False):
        # sqlalchemy engine object
        self.engine = None
        self.initial_search_option = None

        # db connection credentials
        # if any are unavailable, raise error.
        try:
            self.user = os.environ["AUGUR_USERNAME"]
            self.password = os.environ["AUGUR_PASSWORD"]
            self.host = os.environ["AUGUR_HOST"]
            self.port = os.environ["AUGUR_PORT"]
            self.database = os.environ["AUGUR_DATABASE"]
            self.schema = os.environ["AUGUR_SCHEMA"]
        except KeyError as ke:
            logging.critical(f"AUGUR: Database credentials incomplete: {ke}")
            raise KeyError(ke)

        # oauth endpoints have to be intact to proceed
        if handles_oauth:
            try:
                # application credentials
                self.app_id = os.environ["AUGUR_APP_ID"]
                self.client_secret = os.environ["AUGUR_CLIENT_SECRET"]

                # user-level endpoints
                self.session_generate_endpoint = os.environ["AUGUR_SESSION_GENERATE_ENDPOINT"]
                self.user_groups_endpoint = os.environ["AUGUR_USER_GROUPS_ENDPOINT"]
                self.user_account_endpoint = os.environ["AUGUR_USER_ACCOUNT_ENDPOINT"]
                self.user_auth_endpoint = os.environ["AUGUR_USER_AUTH_ENDPOINT"]

                # admin-level endpoints
                self.admin_name_endpoint = os.environ["AUGUR_ADMIN_NAME_ENDPOINT"]
                self.admin_group_names_endpoint = os.environ["AUGUR_ADMIN_GROUP_NAMES_ENDPOINT"]
                self.admin_groups_endpoint = os.environ["AUGUR_ADMIN_GROUPS_ENDPOINT"]
            except KeyError as ke:
                logging.critical(f"AUGUR: Oauth endpoints incomplete: {ke}")

    def get_engine(self):
        """
        Creates _engine.Engine object connected to our Augur database.

        Returns:
        --------
            _engine.Engine: SQLAlchemy engine object.
        """

        # return engine immediately if it already exists
        if self.engine:
            return self.engine

        database_connection_string = "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
            self.user, self.password, self.host, self.port, self.database
        )

        engine = salc.create_engine(
            database_connection_string,
            connect_args={"options": "-csearch_path={}".format(self.schema)},
            pool_pre_ping=True,
        )

        # verify that engine works
        try:
            # context managed connect, closes automatically
            with engine.connect() as conn:
                logging.warning("AUGUR: Connection to DB succeeded")

            self.engine = engine

        except SQLAlchemyError as err:
            logging.error(f"AUGUR: DB couldn't connect: {err.__cause__}")
            raise SQLAlchemyError(err)

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

        try:
            with self.engine.connect() as conn:
                result_df = pd.read_sql(query, con=conn)
        except:
            raise Exception("DB Read Failure")

        result_df = result_df.reset_index()
        result_df.drop("index", axis=1, inplace=True)

        return result_df

    def multiselect_startup(self):
        logging.warning(f"MULTISELECT_STARTUP")

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
        logging.warning(f"MULTISELECT_QUERY")

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
        # self.repo_id_to_repo_git = {value: key for (key, value) in self.repo_git_to_repo_id.items()}
        self.repo_id_to_repo_git = pd.Series(df_repo_git_id.repo_git.values, index=df_repo_git_id["repo_id"]).to_dict()

        logging.warning(f"MULTISELECT_FINISHED")

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

    def repo_id_to_git(self, id):
        """Getter method for dictionary
        that converts a repo_id to the respective
        git URL in the source db.
        Args:
            int: repo_id of the URL in the source DB.
        Returns:
            git (str): URL of repo
        """
        return self.repo_id_to_repo_git.get(id)

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
        """Getter method for the initial multiselect option.
            May be overwritten by the environment.

        Returns:
            dict(value, label): first thing the multiselect will represent on startup
        """
        if self.initial_search_option is None:
            # default the initial multiselect option to the
            # first item in the list of options.
            self.initial_search_option = self.multiselect_options[0]

            if os.getenv("DEFAULT_SEARCHBAR_LABEL"):
                logging.warning("INITIAL SEARCHBAR OPTION: DEFAULT OVERWRITTEN")

                # search through available options for the specified overwriting default.
                for opt in self.multiselect_options:
                    if os.getenv("DEFAULT_SEARCHBAR_LABEL") == opt["label"]:
                        logging.warning(f"INITIAL SEARCHBAR OPTION: NEW DEFAULT: {opt}")
                        self.initial_search_option = opt
                        break

        return self.initial_search_option

    def get_multiselect_options(self):
        """Getter method on all entries in repo+orgs options
        for the multiselect dropdown.

        Returns:
            [{label, value}]: multiselect options
        """
        return self.multiselect_options

    def make_user_request(self, access_token, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}, Bearer {access_token}"

        result = requests.post(self.user_groups_endpoint, headers=headers, params=params)

        if result.status_code == 200:
            return result.json()

    def make_admin_name_request(self, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri
        Added by James Kunstle.

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}"

        result = requests.get(self.admin_name_endpoint, headers=headers, params=params)

        if result.status_code == 200:
            return result.json()

    def make_admin_group_names_request(self, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri
        Added by James Kunstle.

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}"

        result = requests.get(self.admin_group_names_endpoint, headers=headers, params=params)

        if result.status_code == 200:
            return result.json()

    def make_admin_groups_request(self, headers={}, params={}):
        """Large parts of code written by John McGinness, University of Missouri
        Added by James Kunstle.

        Returns:
            _type_: _description_
        """
        headers["Authorization"] = f"Client {self.client_secret}"

        result = requests.get(self.admin_groups_endpoint, headers=headers, params=params)

        if result.status_code == 200:
            return result.json()
