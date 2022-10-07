from tkinter import W
import dash
from app import augur_db
import plotly.graph_objects as go
import logging

columns = ["1", "2", "3"]

# graph displayed while data is downloading
temp_graph = go.Figure([go.Bar(x=columns, y=[20, 14, 23])])
temp_graph.update_traces(
    marker_color="rgb(230,230,230)", marker_line_color="rgb(200,200,300)", marker_line_width=1.5, opacity=0.33
)
temp_graph.update_layout(
    title={"text": "Downloading and Processing Data", "y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"},
    font=dict(size=18, color="black"),
)

# graph displayed if no data is available
nodata_graph = go.Figure([go.Bar(x=columns, y=[20, 14, 23])])
nodata_graph.update_traces(
    marker_color="rgb(230,230,230)", marker_line_color="rgb(200,200,300)", marker_line_width=1.5, opacity=0.6
)
nodata_graph.update_layout(
    title={"text": "No Available Data", "y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"},
    font=dict(size=18, color="red"),
)

# graph displayed if a worker fails
timeout_graph = go.Figure([go.Bar(x=columns, y=[20, 14, 23])])
timeout_graph.update_traces(
    marker_color="rgb(230,230,230)", marker_line_color="rgb(200,200,300)", marker_line_width=1.5, opacity=0.6
)
timeout_graph.update_layout(
    title={"text": "No Available Data", "y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"},
    font=dict(size=18, color="orange"),
)


def handle_job_state(jm, func, repolist):
    """
    Handle the state of a specific Job in the Queue object.
    Code used by visualization callbacks to manage Job
    enqueuement, status-checking, and result-getting.

    Args:
    -----
        jm (JobManager): Object that handles Jobs in Queue object in Redis.
        func (function): Function that worker picks up to run as job.
        repolist ([str]): Arguments to function, list of repos.

    Returns:
    --------
        ready (boolean): Is True if the results from the Job are ready to be consumed, else False.
        results ({[]} | None): Are not None if results are ready.
        temp_graph (px.Figure): Loading graph of RepoList processing steps, per repo.
        timer_set (int | dash.no_update): 0 if timer (dcc.Interval) is being set to run again, else dash.no_update.
    """

    # job status, job results.
    status, results = jm.get_results(func, repolist)

    # results aren't ready
    if results is None:

        # job doesn't exists
        if status is None:

            # create new job
            jm.add_job(func, augur_db.package_config(), repolist)

            # Job not ready, no results, display temp graph, set timer to run again.
            return (False, None, temp_graph, 0)

        # job exists, in one of running states
        elif status in ["queued", "started", "finished"]:

            # Job not ready, no results, display temp graph, set timer to run again.
            return (False, None, temp_graph, 0)

        # job not in healthy state
        else:

            # Job not ready, no results, display timeout graph, don't reset timer.
            return (False, None, timeout_graph, dash.no_update)

    else:

        # Job ready, results included, no graph, don't reset timer.
        return (True, results, None, dash.no_update)
