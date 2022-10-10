from redis import Redis
from rq import Queue, Retry
from queries.commits_query import commits_query
from queries.contributors_query import contributors_query
from queries.issues_query import issues_query

import os
import hashlib
import logging


class JobManager:
    """
    A class that wraps the RQ worker interface (enqueuement and return retrieval).
    Does not abstract the choices-to-be-made based on a job's status and availability.

    Attributes
    ----------
        _redis : (private) Redis object
            Manager for Redis in-memory cache that hosts queue for RQ workers
            and RQ worker results.

        _rq : (private) Queue object
            Queue onto which jobs are pushed, FIFO, for RQ workers to pick up.

        
    Methods
    -------
        _get_job_hash(func, arglist) (private) :
            Creates a unique hash for each job based on the job's calling
            function and the list of repos that the function is being run with.

        add_job(func, dbmc, repolist) :
            Enqueues job onto Queue object hosted on Redis for RQ worker to pick
            up later, keyed by job_hash.

        get_job(func, arglist) :
            Gets most updated job from Queue object, if its job_hash ID exists.

        get_results(func, arglist) :
            Returns the status of a job and the results from that job, if they exist.

        job_refreshed(job) : 
            Returns job-object refreshed with most updated contents from Queue, if
            it exists.

        get_job_status(func, arglist) :
            Returns a job's status, if it exists.
    
    """
    def __init__(self):
        # Redis cache for job queue and results cache
        self._redis = Redis(
            # openshift will reconcile the 'redis' naming via the dns
            host=os.getenv("REDIS_SERVICE_HOST", "localhost"),
            port=os.getenv("REDIS_SERVICE_PORT", "6379"),
            password=os.getenv("REDIS_PASSWORD", ""),
        )
        # RQ service connected to Redis
        self._rq = Queue(connection=self._redis, default_timeout=600)

    def _get_job_hash(self, func, repo):
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

    def add_job(self, func, dbmc, repo):
        """
        Adds job to Queue object hosted in Redis.

        Args:
        -----
            func (function): Function that worker picks up to run as job.
            dbmc (AugurInterface class): DatabaseManagerClass, handles access to database of community data.
            repo (str): Argument to function. Repo data downloaded for.

        Returns:
        --------
            _Hash: Unique key in Queue object to access job status and results.
        """

        # get a hash of the function used and the args supplied
        job_hash = self._get_job_hash(func, repo)

        # add a job to our queue, 1 day timeout (86400 sec), id of its hash, retry if failed
        job = self._rq.enqueue(func, dbmc, repo, job_id=job_hash, result_ttl=86400, retry=Retry(max=3, interval=[5, 10, 15]))

        return job_hash

    def get_job(self, func, repo):
        """
        Gets job object from Queue object in Redis instance, if it exists.
        Keyed by its job_hash.

        Returns None if job isn't in Queue.

        Args:
        -----
            func (function): Function that worker picks up to run as job.
            repo (str): Argument to function. Repo data downloaded for.

        Returns:
        --------
            Job | None: Reference to Job object or None 
        """

        # get an identifying hash of the function used and the args supplied
        job_hash = self._get_job_hash(func, repo)

        # grab the job from the job queue
        job = self._rq.fetch_job(job_hash)

        # check if job was fetched from queue
        if job is not None:
            return job
        # if job didn't exist, nothing to return.
        else:
            return None

    def get_results(self, func, repo):
        """
        Gets status and results from Job in Queue object,
        if job exists.

        If Job doesn't exist by job_hash, returns None.

        Args:
        -----
            func (function): Function that worker picks up to run as job.
            repo (str): Argument to function. Repo data downloaded for.

        Returns:
        --------
            state (str) | None: State of the Job object in the Queue or None
            results ([[Any]]) | None: Results from the worker's finished Job, is a list of lists, or None.
        """

        # check to see if job already exists.
        job = self.get_job(func, repo)

        # does job exist by ID in Queue?
        if job is not None:

            # refresh job object from Redis
            job = self.job_refreshed(job)

            # job could now be none if Cache wasn't up to date.
            if job is None:
                return (None, None)

            # job definitely finished, check if results are available
            if job.ended_at is not None:

                # results not available
                if job.result is not None:

                    # is finished, results available
                    return (job.get_status(), job.result)

            # job not finished, no results.
            return (job.get_status(), None)

        else:
            # job didn't exist in Queue in any state.
            return (None, None)

    def job_refreshed(self, job):
        """
        Refreshes Job object metadata if the job exists in the Queue.

        Args:
        -----
            job (Job): Job object

        Returns:
        --------
            Job | None: Refreshed Job object with updated metadata or None.
        """
        try:
            # try to grab all of the new object values for a job
            job.refresh()
            return job
        except:
            # job not cached any more, is None.
            # don't neet to delete job from _jobs
            # because add_job will handle that.
            return None

    def get_job_status(self, func, repo):
        """
        Current status of Job in Queue, if it exists.
        
        None if Job not in Queue.

        Args:
        -----
            func (function): Function that worker picks up to run as job.
            arglist ([str]): Arguments to function, list of repos.

        Returns:
        --------
            state (str) | None: State of the Job object in the Queue or None
        """

        # check to see if job exists.
        job = self.get_job(func, repo)

        # if job exists, return its status
        if job is not None:
            return job.get_status(refresh=True)
        # otherwise None
        else:
            return None
