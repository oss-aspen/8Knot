from redis import Redis
from rq import Queue
from queries.commits_query import commits_query
from queries.contributors_query import contributors_query
from queries.issues_query import issues_query

import os
import hashlib
import logging


class JobManager:
    def __init__(self):
        # Redis cache for job queue and results cache
        self._redis = Redis(
            # openshift will reconcile the 'redis' naming via the dns
            host=os.getenv("REDIS_SERVICE_HOST", "localhost"),
            port=os.getenv("REDIS_SERVICE_PORT", "6379"),
            password=os.getenv("dbpw", ""),
        )
        # RQ service connected to Redis
        self._rq = Queue(connection=self._redis)

    def _get_job_hash(self, func, arglist):

        # use md5 instead of sha256 or better because
        # we're only ensuring limited collision avoidance, not
        # practicing good securiy protocol.
        hashfunc = hashlib.md5()
        # use the called function's name
        hashfunc.update(bytes(func.__name__, "utf-8"))
        # and the repo list we're passing to it
        hashfunc.update(bytes(str(frozenset(arglist)), "utf-8"))
        # grab the hex hash that's been generated.
        h = hashfunc.hexdigest()

        return h

    # dbmc is "database manager config"
    def add_job(self, func, dbmc, repolist):

        # get a hash of the function used and the args supplied
        job_hash = self._get_job_hash(func, repolist)

        # add a job to our queue, 10 minute timeout (6000ms), id of it's hash.
        job = self._rq.enqueue(func, dbmc, repolist, job_id=job_hash, job_timeout=6000)

        return job_hash

    def get_job(self, func, arglist):

        # get an identifying hash of the function used and the args supplied
        job_hash = self._get_job_hash(func, arglist)

        # grab the job from the job queue
        job = self._rq.fetch_job(job_hash)

        # check if job was fetched from queue
        if job is not None:
            logging.debug(f"CACHE HIT: {func.__name__}")
            return job
        # if job didn't exist, nothing to return.
        else:
            return None

    def get_results(self, func, arglist):

        # check to see if job already exists.
        job = self.get_job(func, arglist)

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
        try:
            # try to grab all of the new object values for a job
            job.refresh()
            return job
        except:
            # job not cached any more, is None.
            # don't neet to delete job from _jobs
            # because add_job will handle that.
            return None

    def get_job_status(self, func, arglist):

        # check to see if job exists.
        job = self.get_job(func, arglist)

        # if job exists, return its status
        if job is not None:
            return job.get_status(refresh=True)
        # otherwise None
        else:
            return None
