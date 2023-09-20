from redis import StrictRedis
import os
import hashlib
import pandas as pd
import io
import sys
import logging


class CacheManager:
    """
    Manages access to Redis cache.

    Attributes
    ----------
        _redis : (private) Redis object

    Methods
    -------
        _get_hash(func, repo) (private) :
            Creates a unique hash for each job based on the job's calling
            function and the list of repos that the function is being run with.

        set(func, repo, data) :
            Sets data at key hash(func, repo).

        setm(func, [repo], [data]) :
            Sets [data] at keys [hash(func, repo)] of [repo]

        get(func, repo):
            Returns data at key hash(func, repo), None if Nil.

        getm(func, [repo]):
            Returns data at keys [hash(func, repo)], None if Nil.
            Uses r.mget([keys])

        exists(func, repo):
            Returns number of names that exist.

        existsm(func, [repo]):
            Returns number of names that exist.

    """

    def __init__(self, decode_value=False):
        # Redis cache for job queue and results cache
        self._redis = StrictRedis(
            # openshift, compose will reconcile the 'redis' naming via the dns
            host=os.getenv("REDIS_SERVICE_HOST", "redis-cache"),
            port=os.getenv("REDIS_SERVICE_PORT", "6379"),
            password=os.getenv("REDIS_PASSWORD", ""),
            decode_responses=decode_value,
        )

    def _get_hash(self, func, repo):
        """
        (private)
        Creates an MD5-hash based on the string-bytes
        of the passed function and the list of repos that
        the function is going to be run on.

        Hash is used as a key by which the status of and results from the
        worker are accessed from the Queue.

        Args:
        -----
            func (function): Function that worker picks up to run as job.
            repo (str): Argument to function. Repo data downloaded for.

        Returns:
        --------
            _Hash: Unique key in Queue object to access job status and results.
        """

        # use md5 instead of sha256 or better because
        # we're only ensuring limited collision avoidance, not
        # practicing good securiy protocol.
        hashfunc = hashlib.md5()

        # use the called function's name
        hashfunc.update(bytes(func.__name__, "utf-8"))

        # and the repo list we're passing to it
        hashfunc.update(bytes(str(repo), "utf-8"))
        # grab the hex hash that's been generated.
        h = hashfunc.hexdigest()

        return h

    def set(self, func, repo, data):
        """Sets redis value as data at name=hash(func, repo)

        Args:
            func (function): Query function used
            repo (int): repo_id of repo
            data (list(dict)): rows of data in dictionary format.

        Returns:
            boolean: confirmation of successful set operation.
        """

        # set redis value at 'name=hash' to 'data'
        ack = self._redis.set(name=self._get_hash(func=func, repo=repo), value=data)

        return ack

    def setm(self, func, repos, datas):
        """Sets many redis value as data at name=hash(func, repo)

        Args:
            func (function): Query function used
            repo (list[int]): list of repo_ids of repos
            data (list[list(dict)]): list of rows of data in dictionary format.

        Returns:
            list[boolean]: confirmations of successful set operations.
        """

        # create hashes for each (func, repo_id) pair
        hs = [self._get_hash(func, r) for r in repos]
        ds = datas

        # bulk-set keys to values in Redis
        acks = self._redis.mset(dict(zip(hs, ds)))

        # from redis docs: "(Return is) always OK since MSET can't fail."
        return acks

    def get(self, func, repo):
        """Get redis value as data at name=hash(func, repo)

        Args:
            func (function): Query function used
            repo (int): list of repo_id of repo

        Returns:
            boolean: confirmation of successful set operation.
        """

        # get redis value at "name=hash"
        r = self._redis.get(name=self._get_hash(func, repo))

        return r

    def getm(self, func, repos):
        """Gets many redis value as data at name=hash(func, repo)

        Args:
            func (function): Query function used
            repo (list[int]): list of repo_ids of repos

        Returns:
            (list[list(dict)]): list of rows of data in dictionary format.
        """

        # create hashes for each (func, repo_id) pair
        hs = [self._get_hash(func, r) for r in repos]

        # bulk-get values from keys in Redis
        rs = self._redis.mget(hs)

        # return results
        return rs

    def exists(self, func, repo):
        """Checks whether key is in Redis for hash(func, repo)

        Args:
            func (function): Query function used
            repo (int): repo_id of repo

        Returns:
            int: number of names that exist
        """

        # convert single value into a list
        repo = [repo]

        # pass to exists_many, processes as a list.
        return self.existsm(func, repo)

    def existsm(self, func, repos):
        """Checks whether keys are in Redis for hash(func, repo)

        Args:
            func (function): Query function used
            repo (list[int]): list of repo_ids of repos

        Returns:
            int: number of names that exist
        """

        # create hashes for each (func, repo_id) pair
        hs = [self._get_hash(func, r) for r in repos]

        # bulk-get values from keys in Redis
        n = self._redis.exists(*hs)

        # return results
        return n

    def grabm(self, func, repos):
        """Checks to see if data is ready using 'existsm'
        and builds aggregate DataFrame to return to callback.

        Args:
            func (function): Query function used
            repo (list[int]): list of repo_ids of repos

        Returns:
            pd.DataFrame | None: Data if all available.
        """

        num_repos = len(repos)
        ready = self.existsm(func=func, repos=repos) == num_repos
        if not ready:
            return None

        # get all results from cache
        dfs_from_cache = self.getm(func=func, repos=repos)

        pd_dfs = []
        for bdf in dfs_from_cache:
            bbuff = io.BytesIO(bdf)
            bbuff.seek(0)
            df = pd.read_feather(bbuff)
            pd_dfs.append(df)

        out_df = pd.concat(pd_dfs)

        return out_df
