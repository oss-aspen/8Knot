from tkinter import W
import dash
from app import augur_db
import plotly.graph_objects as go
import logging
import pandas as pd

columns = ["1", "2", "3"]

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

def _loading_graph(done, queued, retry, failed):
    colors = ['gold', 'mediumturquoise', 'lightgreen', 'black']

    fig = go.Figure(
        data=[
            go.Pie(
                    labels=['Done','Queued', 'Retry', 'Failed'],
                    values=[done, queued, retry, failed]
                )
            ]
        )
    fig.update_traces(hoverinfo='label', textinfo='value', textfont_size=20,
                    marker=dict(colors=colors, line=dict(color='#000000', width=2)))

    return fig

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
    num_done = 0
    num_failed = 0
    num_retry = 0
    num_total = len(repolist)

    for repo in repolist:

        # job status, job results.
        status, results = jm.get_results(func, repo)

        # results aren't ready
        if results is None:

            # job doesn't exists
            if status is None:

                # create new job
                jm.add_job(func, augur_db.package_config(), repo)

                # Job not ready, no results, display temp graph, set timer to run again.
                # return (False, None, temp_graph, 0)

            # job exists, in one of running states
            elif status in ["queued", "started", "finished"]:
                pass

            elif status == "scheduled":
                logging.error(f"Job failed and was rescheduled.")
                num_retry += 1

            # job not in healthy state
            else:

                # Job not ready, no results, display timeout graph, don't reset timer.
                # return (False, None, timeout_graph, dash.no_update)
                num_failed += 1
                logging.critical(f"Job failed; status: {status}")

        else:

            num_done += 1
            # Job ready, results included, no graph, don't reset timer.
            # return (True, results, None, dash.no_update)

    if num_done == num_total:
        
        out = [] 
        for repo in repolist:

            stat, res = jm.get_results(func, repo)

            # merge the lists together
            if res is not None:
                out += res           

        # Job ready, results included, no graph, don't reset timer.
        return (True, out, None, dash.no_update) 
    
    else:
        loading_graph = _loading_graph(
            num_done,
            num_total - (num_done + num_failed),
            num_retry,
            num_failed
        )

        return (False, None, loading_graph, 0)
