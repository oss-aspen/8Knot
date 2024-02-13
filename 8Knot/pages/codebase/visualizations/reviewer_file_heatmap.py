from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.contributors_query import contributors_query as cnq
from queries.cntrb_per_file_query import cntrb_per_file_query as cpfq
from queries.repo_files_query import repo_files_query as rfq
from app import augur
from pages.utils.job_utils import nodata_graph
import pages.utils.preprocessing_utils as preproc_u
import time
from dash.exceptions import PreventUpdate
import app
import cache_manager.cache_facade as cf

PAGE = "codebase"
VIZ_ID = "reviewer-file-heatmap"

# div to hold all objects to wait for loading to render
graph_loading = html.Div(
    [
        dbc.Popover(
            [
                dbc.PopoverHeader("Graph Info:"),
                dbc.PopoverBody(
                    """
                    This visualization analyzes the activity of the reviewers to sub-sections (files or folders)
                    of a repository. Specifically, this heatmap identifies the last time a sub-section's reviewer
                    (those people who have reviewed at least one pull request to a sub-section) last contributed to the
                    repository. See the definition of "contribution" on the Info page for more information. This could be
                    interpreted as monitoring technical knowledge retention of codebase components: if a sub-section's
                    past reviewers are no longer active in the repository, maintainership of that sub-section could
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

gc_reviewer_file_heatmap = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Reviewer File Heatmap",
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
    # array to hold repo_id and git url pairing for dropdown
    data_array = []
    for repo_id in repo_ids:
        entry = {"value": repo_id, "label": augur.repo_id_to_git(repo_id)}
        data_array.append(entry)
    return data_array, repo_ids[0]


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
    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=rfq.__name__, repolist=[repo_id]):
        logging.warning(f"DIRECTORY DROPDOWN - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    logging.warning(f"DIRECTORY DROPDOWN - RETRIEVING FROM CACHE")
    df = cf.retrieve_from_cache(
        tablename=rfq.__name__,
        repolist=[repo_id],
    )

    logging.warning(f"DIRECTORY DROPDOWN - CACHE READ")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} DROPDOWN- NO DATA AVAILABLE")
        return ["Top Level Directory"], "Top Level Directory"

    # strings to hold the values for each column (always the same for every row of this query)
    repo_name = df["repo_name"].iloc[0]
    repo_path = df["repo_path"].iloc[0]
    repo_id = str(df["repo_id"].iloc[0])

    # pattern found in each file path, used to slice to get only the root file path
    path_slice = repo_id + "-" + repo_path + "/" + repo_name + "/"
    df["file_path"] = df["file_path"].str.rsplit(path_slice, n=1).str[1]

    # drop columns not in the most recent collection
    df = df[df["rl_analysis_date"] == df["rl_analysis_date"].max()]

    # drop unneccessary columns not needed after preprocessing steps
    df = df.reset_index()
    df.drop(
        ["index", "repo_id", "repo_name", "repo_path", "rl_analysis_date"],
        axis=1,
        inplace=True,
    )

    # split file path by directory
    df = df.join(df["file_path"].str.split("/", expand=True))

    # take all of the files, split on the last instance of a / to get directories and top level files
    directories = df["file_path"].str.rsplit("/", n=1).str[0].tolist()
    # applies another rsplit to make sure directories that only have folders are included
    folder_only_directories = [x.rsplit("/", 1)[0] for x in directories]
    directories = list(set(directories + folder_only_directories))

    # get all of the file names to filter out of the directory set
    top_level_files = df["file_name"][df[1].isnull()].tolist()
    directories = [f for f in directories if f not in top_level_files]

    # sort alphabetically
    directories = sorted(directories)

    # add top level directory to the list of directories
    directories.insert(0, "Top Level Directory")
    logging.warning(f"DIRECTORY DROPDOWN - FINISHED")

    return directories, "Top Level Directory"


# callback for reviewer file heatmap graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input(f"repo-{PAGE}-{VIZ_ID}", "value"),
        Input(f"directory-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def reviewer_file_heatmap_graph(repo_id, directory, bot_switch):
    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # get dataframes of data from cache
    df_file, df_actions, df_file_cntbs = multi_query_helper([repo_id])

    # test if there is data
    if df_file.empty or df_actions.empty or df_file_cntbs.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing
    df = process_data(df_file, df_actions, df_file_cntbs, directory, bot_switch)

    # if there are no cntrbs in a directory plot no data graph
    if df.empty:
        return nodata_graph

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def multi_query_helper(repos):
    """
    For reviewer_file_heatmap_graph-
    hack to put all of the cache-retrieval
    in the same place temporarily
    """

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=rfq.__name__, repolist=repos):
        logging.warning(f"CONTRIBUTOR FILE HEATMAP - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=cnq.__name__, repolist=repos):
        logging.warning(f"CONTRIBUTOR FILE HEATMAP - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # wait for data to asynchronously download and become available.
    while not_cached := cf.get_uncached(func_name=cpfq.__name__, repolist=repos):
        logging.warning(f"CONTRIBUTOR FILE HEATMAP - WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    # GET ALL DATA FROM POSTGRES CACHE
    df_file = cf.retrieve_from_cache(
        tablename=rfq.__name__,
        repolist=repos,
    )
    df_actions = cf.retrieve_from_cache(
        tablename=cnq.__name__,
        repolist=repos,
    )
    df_file_cntrbs = cf.retrieve_from_cache(
        tablename=cpfq.__name__,
        repolist=repos,
    )

    # necessary preprocessing steps that were lifted out of the querying step
    df_actions = preproc_u.contributors_df_action_naming(df_actions)
    df_file_cntrbs = preproc_u.cntrb_per_file(df_file_cntrbs)

    return df_file, df_actions, df_file_cntrbs


def process_data(
    df_file: pd.DataFrame,
    df_actions: pd.DataFrame,
    df_file_cntbs: pd.DataFrame,
    directory,
    bot_switch,
):

    # df_file preprocessing
    df_file = df_file_clean(df_file, df_file_cntbs, bot_switch)

    df_dynamic_directory = cntrb_per_directory_value(directory, df_file)

    # work around for using functions, will clean later
    if df_dynamic_directory.empty:
        return df_dynamic_directory

    df_dynamic_directory = cntrb_to_last_activity(df_actions, df_dynamic_directory)

    final = file_cntrb_activity_by_month(df_dynamic_directory, df_actions)

    return final


def create_figure(df: pd.DataFrame):
    fig = px.imshow(
        df,
        labels=dict(x="Time", y="Directory Entries", color="Contributors"),
        color_continuous_scale=px.colors.sequential.deep,
    )

    fig["layout"]["yaxis"]["tickmode"] = "linear"
    fig["layout"]["height"] = 700
    fig["layout"]["coloraxis_colorbar_x"] = -0.15
    fig["layout"]["yaxis"]["side"] = "right"

    return fig


def df_file_clean(df_file: pd.DataFrame, df_file_cntbs: pd.DataFrame, bot_switch):
    # strings to hold the values for each column (always the same for every row of this query)
    repo_name = df_file["repo_name"].iloc[0]
    repo_path = df_file["repo_path"].iloc[0]
    repo_id = str(df_file["repo_id"].iloc[0])

    # pattern found in each file path, used to slice to get only the root file path
    path_slice = repo_id + "-" + repo_path + "/" + repo_name + "/"
    df_file["file_path"] = df_file["file_path"].str.rsplit(path_slice, n=1).str[1]

    # drop unneccessary columns not needed after preprocessing steps
    df_file = df_file.reset_index()
    df_file.drop(["index", "repo_name", "repo_path", "rl_analysis_date"], axis=1, inplace=True)

    # split file path by directory
    df_file = df_file.join(df_file["file_path"].str.split("/", expand=True))

    # drop unnecessary columns
    df_file.drop(["repo_id"], axis=1, inplace=True)
    df_file_cntbs.drop(["repo_id", "cntrb_ids"], axis=1, inplace=True)

    # Left join on df_files to only get the files that are currently in the repository
    # and the contributors that have ever reviewed a pr that included edits on the file
    df_file = pd.merge(df_file, df_file_cntbs, on="file_path", how="left")
    # replace nan with empty string to avoid errors in list comprehension
    df_file.reviewer_ids.fillna("", inplace=True)

    # reformat reviewer_ids to list and remove bots if filter is on
    if bot_switch:
        df_file["reviewer_ids"] = df_file.apply(
            lambda row: [x for x in row.reviewer_ids if x not in app.bots_list],
            axis=1,
        )
    else:
        df_file["reviewer_ids"] = df_file.apply(
            lambda row: [x for x in row.reviewer_ids],
            axis=1,
        )

    return df_file


def cntrb_per_directory_value(directory, df_file):
    # determine directory level to use in later step
    level = directory.count("/")
    if directory == "Top Level Directory":
        level = -1
        directory = ""

    # get all of the files in the directory or nested in folders in the directory
    df_dynamic_directory = df_file[df_file["file_path"].str.startswith(directory)]

    # number of files in the directory or nested in folders in the directory that have no contributors
    num_empty_cntrb = df_dynamic_directory[df_dynamic_directory["reviewer_ids"].str.len() == 0].shape[0]

    # return empty df if all of the files in the directory or nested in folders in the directory have
    # no contributors
    if num_empty_cntrb == df_dynamic_directory.shape[0]:
        return pd.DataFrame()

    # get one level up from the directory level
    group_column = level + 1

    # Groupby the level above the selected directory for all files nested in folders are together.
    # For each, create a list of all of the contributors who have contributed
    df_dynamic_directory = (
        df_dynamic_directory.groupby(group_column)["reviewer_ids"]
        .sum()
        .reset_index()
        .rename(columns={group_column: "directory_value"})
    )

    # Set of reviewer_ids to confirm there are no duplicate reviewer_ids
    df_dynamic_directory["reviewer_ids"] = df_dynamic_directory.apply(
        lambda row: set(row.reviewer_ids),
        axis=1,
    )
    return df_dynamic_directory


def cntrb_to_last_activity(df_actions: pd.DataFrame, df_dynamic_directory: pd.DataFrame):

    # date reformating
    df_actions["created_at"] = pd.to_datetime(df_actions["created_at"], utc=True)

    # sort by created_at date latest to earliest and only keep a contributors most recent activity
    df_actions = df_actions.sort_values(by="created_at", axis=0, ascending=False)
    df_actions = df_actions.drop_duplicates(subset="cntrb_id", keep="first")

    # drop unneccessary columns not needed after preprocessing steps
    df_actions = df_actions.reset_index()
    df_actions.drop(
        ["index", "repo_id", "repo_name", "login", "Action", "rank"],
        axis=1,
        inplace=True,
    )

    # dictionary of reviewer_ids and their most recent activity on repo
    last_contrb = df_actions.set_index("cntrb_id")["created_at"].to_dict()

    # get list of dates of the most recent activity for each contributor for each file
    df_dynamic_directory["dates"] = df_dynamic_directory.apply(
        lambda row: [last_contrb[x] for x in row.reviewer_ids],
        axis=1,
    )

    # reformat into each row being a directory value and a date of one of the contributors
    # most recent activity - preprocessing step
    df_dynamic_directory = df_dynamic_directory.explode("dates")

    return df_dynamic_directory


def file_cntrb_activity_by_month(df_dynamic_directory: pd.DataFrame, df_actions: pd.DataFrame):

    # get files that have no contributors and remove from set to prevent errors in grouper function
    no_contribs = df_dynamic_directory["directory_value"][df_dynamic_directory.dates.isnull()].tolist()

    df_dynamic_directory = df_dynamic_directory[~df_dynamic_directory.dates.isnull()]

    """Creates df with a column for each month between start and end date. This will be used to confirm that
    there will be a column for every month even if there is no "last contribution" date in it. This greatly
    improves the heatmap ploting"""

    # dates based on action so it represents the length of the project
    min_date = df_actions.created_at.min()
    max_date = df_actions.created_at.max()
    dates = pd.date_range(start=min_date, end=max_date, freq="M", inclusive="both")
    df_fill = dates.to_frame(index=False, name="dates")

    # combine df with data and filler dates together
    final = pd.concat([df_dynamic_directory, df_fill], axis=0)
    final["directory_value"] = final["directory_value"].astype(str)

    # grouping dates by every month and counting the number of contributors with the last activity at that date
    final = final.groupby(pd.Grouper(key="dates", freq="1M"))["directory_value"].value_counts().unstack(0)

    # removing the None row that was used for column formating
    final.drop("nan", inplace=True)

    # add back the files that had no contributors
    for files in no_contribs:
        final.loc[files] = None

    return final
