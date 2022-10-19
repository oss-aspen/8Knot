# Explorer Worker Architecture

## Background

Our Dash application's server is stateless by architecture.

From the perspective of the server, all incoming requests are anonymous, meaning that the server is only aware of the request itself, not which client has sent the request.

This is highly performant because we can arbitrarily scale our application by duplicating server instances; no user context data must be shared between the servers themselves, and user requests can be load-balanced naively.

## Job-Queue Motivation

To bolster the responsiveness of this app, it is ideal for the resources dedicated to serving user requests to be allocated separately from those used to do any hard work.

For our purposes this is a solved problem with a well-documented design pattern: if we know that a task would take more than a reasonable amount of time to run and would consume relatively more than minimal resources, we can add that task to a queue data structure to be processed later.

Workers, with resources allocated separately from those that serve client requests, take jobs from this queue in order and publish the results from these jobs in a cache.

The webserver polls the cache for the results from the workers and uses them when they become available.

## Technical Architecture

We implement a scalable and minimalist job queue that resolves previous application responsiveness and server-timeout challenges.

### Queries

The longest-running tasks our app runs are SQL queries to our instance of an Augur database. These can take as little as 500ms to resolve but in the worst case it can take up to 15 minutes to get a response. These are I/O-bound tasks so they could be solved by implementing naive multi-threading, but a job-queue design is far more easily scalable.

### RQ

We enqueue our long-running queries in a Queue object implemented by the RQ (Redis Queue) python library. RQ executes a specified function (passed by reference) in its own Python process (with a separate GIL). Arguments to this function are passed via pickling. This can be a problem for non-picklable objects but there are simple workarounds.

### Redis

Redis is an in-RAM data structure store library. RQ implements its queue structure using Redis, and the results of a worker's task are cached in the Redis data store, accessible by reference.

### Dash Server

When the client requests a visualization based on the data of a group of repos, the server first checks if the results of a previous worker would fulfill this request. This is done by checking if the deterministic hash composed of the inputs (function name) and (set of repository ID's) is currently in the Redis cache.

If the cache is cold, a job is added to the queue with the reference of that hash, accessible by the calling thread and future server processes with access to that cache.

The job object is enqueued and is later processed by the workers managed by RQ. When a worker's thread of execution finishes, it returns its result and is destroyed. The result is cached in Redis for a parameterized length of time.

The server routinely polls the job it created for its results. When the job's metadata confirms that the results are ready, the server can use them for its next steps.

## Conclusion

This architecture is minimally configured and low-overhead, likely requiring very little maintenance. It is likely that worker management by the Supervisor module will be effective in the future if OpenShift scaling isn't a satisfying solution.
