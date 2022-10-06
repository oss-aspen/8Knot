"""
    Imports
"""
from re import I
import pandas as pd
import sqlalchemy as salc
import json
import os
import logging


class AugurInterface:
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
            Loads credentials for AugurInterface object from a pconfig.
            We need to do this because _engine.Engine objects can't be pickled and
            passed as parameters to workers via Queue objects.
    """
    def __init__(self):
        self.pconfig = False
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
        Creates _engine.Engine object connected to our Augur database.

        Returns:
        --------
            _engine.Engine: SQLAlchemy engine object. 
        """
        if self.engine is not None:
            return self.engine

        if self.config_loaded is False and not self.pconfig:

            
            # make sure all of the environment variables are available
            env_values = ["user", "password", "host", "port", "database", "schema"]
            for v in env_values:

                if v not in os.environ:
                    logging.critical(f"Required environment variable \"{v}\" not available.")
                    return None

                if os.getenv(v) is None:
                    logging.critical(f"Required environment variable: \"{v}\" available but none.")
                    return None
            
            # have confirmed that necessary environment variables exist- proceed.
            self.user = os.getenv("user")
            self.password = os.getenv("password")
            self.host = os.getenv("host")
            self.port = os.getenv("port")
            self.database = os.getenv("database")
            self.schema = os.getenv("schema")
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

        this_df = pd.DataFrame()

        pr_query = salc.sql.text(query_string)

        with self.engine.connect() as conn:
            this_df = pd.read_sql(pr_query, con=conn)

        this_df = this_df.reset_index()
        this_df.drop("index", axis=1, inplace=True)

        return this_df

    def package_config(self) -> list(str):
        """
        Packages current credentials into a list for transportation to workers.
        We need to do this because _engine.Engine objects can't be pickled and
        passed as parameters to workers via Queue objects.

        Returns:
        --------
            list(str): List of credentials to recreate same connection to Augur instance.
        """
        if self.config_loaded:
            pconfig = [self.user, self.password, self.host, self.port, self.database, self.schema]
            return pconfig
        else:
            return None

    def load_pconfig(self, pconfig: list):
        """
        Loads credentials for AugurInterface object from a pconfig.
        We need to do this because _engine.Engine objects can't be pickled and
        passed as parameters to workers via Queue objects.

        Args:
        -----
            pconfig (list): Credentials to create AugurInterface object in RQ Workers. 
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
