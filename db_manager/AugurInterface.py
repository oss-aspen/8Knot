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
        Connects to Augur instance using supplied config
        credentials and returns the database engine.
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

    def package_config(self):
        """
        Because we can't pickle this object for workers we
        just ship the config around and create new interface managers
        on the fly as necessary."""
        if self.config_loaded:
            pconfig = [self.user, self.password, self.host, self.port, self.database, self.schema]
            return pconfig
        else:
            return None

    def load_pconfig(self, pconfig: list):
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
