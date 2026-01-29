from dash import html, dcc, callback
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import logging
import time
from pages.utils.job_utils import nodata_graph
from .heatmap_utils import (
    create_repo_dropdown,
    create_directory_dropdown,
    get_activity_heatmap_data,
    process_activity_heatmap,
    create_activity_heatmap_figure,
)

PAGE = "codebase"
VIZ_ID = "cntrb-file-heatmap"

# div to hold all objects to wait for loading to render
graph_loading = html.Div(
    [
        dbc.Popover(
            [
                dbc.PopoverHeader("Graph Info:"),
                dbc.PopoverBody(
                    """
                    This visualization analyzes the activity of the contributors to sub-sections (files or folders)
                    of a repository. Specifically, this heatmap identifies the last time a sub-section's contributors
                    (those people who have opened at least one pull request to a sub-section) last contributed to the
                    repository. See the definition of "contribution" on the Info page for more information. This could be
                    interpreted as monitoring technical knowledge retention of codebase components: if a sub-section's
                    past contributors are no longer active in the repository, maintainership of that sub-section could
                    be insufficient and require attention.
                    """
                ),
            ],
            id=f"popover-{PAGE}-{VIZ_ID}",
            target=f"popover-target-{PAGE}-{VIZ_ID}",
            placement="top",
            is_open=False,
        ),
        dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
        dbc.Form(
            [
                dbc.Row(
                    [
                        dbc.Label(
                            "Select Repository:",
                            html_for=f"repo-{PAGE}-{VIZ_ID}",
                            width="auto",
                        ),
                        dbc.Col(
                            [
                                dmc.Select(
                                    id=f"repo-{PAGE}-{VIZ_ID}",
                                    placeholder="Repo for Heatmap",
                                    classNames={"values": "dmc-multiselect-custom"},
                                    searchable=True,
                                    clearable=True,
                                ),
                            ],
                            className="me-2",
                        ),
                        dbc.Label(
                            "Select Directory:",
                            html_for=f"patterns-{PAGE}-{VIZ_ID}",
                            width="auto",
                        ),
                        dbc.Col(
                            [
                                dmc.Select(
                                    id=f"directory-{PAGE}-{VIZ_ID}",
                                    classNames={"values": "dmc-multiselect-custom"},
                                    searchable=True,
                                    clearable=False,
                                    value="Top Level Directory",
                                ),
                            ],
                            className="me-2",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "About Graph",
                                id=f"popover-target-{PAGE}-{VIZ_ID}",
                                color="secondary",
                                size="sm",
                            ),
                            width="auto",
                            style={"paddingTop": ".5em"},
                        ),
                    ],
                    align="center",
                ),
            ]
        ),
    ],
)

gc_cntrb_file_heatmap = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor File Heatmap",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dcc.Loading(
                    children=graph_loading,
                ),
            ]
        )
    ],
)


# callback for graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for populating repo drop down
@callback(
    [
        Output(f"repo-{PAGE}-{VIZ_ID}", "data"),
        Output(f"repo-{PAGE}-{VIZ_ID}", "value"),
    ],
    [Input("repo-choices", "data")],
)
def repo_dropdown(repo_ids):
    """Create repository dropdown using shared utility function."""
    return create_repo_dropdown(repo_ids, VIZ_ID)


# callback for populating directory drop down
@callback(
    [
        Output(f"directory-{PAGE}-{VIZ_ID}", "data"),
        Output(f"directory-{PAGE}-{VIZ_ID}", "value"),
    ],
    [Input(f"repo-{PAGE}-{VIZ_ID}", "value")],
    background=True,
)
def directory_dropdown(repo_id):
    """Create directory dropdown using shared utility function."""
    directories, default_value = create_directory_dropdown(repo_id, VIZ_ID)
    logging.warning(f"CNTRB DIRECTORY DROPDOWN - FINISHED")
    return directories, default_value


# callback for contributor file heatmap graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"repo-{PAGE}-{VIZ_ID}", "value"),
        Input(f"directory-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def cntrb_file_heatmap_graph(searchbar_repos, repo_id, directory, bot_switch):
    start = time.perf_counter()
    logging.warning(f"{VIZ_ID} - START")

    # get dataframes of data from cache
    df_file, df_actions, df_file_cntbs = get_activity_heatmap_data(searchbar_repos, [repo_id], VIZ_ID)

    # test if there is data
    if df_file.empty or df_actions.empty or df_file_cntbs.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # process data using shared function (contributor IDs)
    df = process_activity_heatmap(df_file, df_actions, df_file_cntbs, directory, bot_switch, "cntrb_ids")

    # if there are no cntrbs in a directory plot no data graph
    if df.empty:
        return nodata_graph

    fig = create_activity_heatmap_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig
