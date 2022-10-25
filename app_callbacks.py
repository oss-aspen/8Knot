from dash import callback
from dash.dependencies import Input, Output, State
import dash
import pandas as pd
import sqlalchemy as salc
import logging
from app import engine, repo_dict, org_dict, all_entries

# helper function for repos to get repo_ids
def _parse_repo_choices(repo_git_set):
    # get repo values from repo dictionary
    repo_values = [repo_dict[x] for x in repo_git_set]
    # values for the repo_ids and names
    repo_ids = [row[0] for row in repo_values]
    repo_names = [row[1] for row in repo_values]

    return repo_ids, repo_names


# helper function for orgs to get repo_ids
def _parse_org_choices(org_name_set):

    # get git urls for the repos in the organization, flatten the 2D list to 1D
    org_repos = sum([org_dict[x] for x in org_name_set], [])
    # get repo values from repo dictionary
    repo_values = [repo_dict[x] for x in org_repos]
    # values for the repo_ids and names
    org_repo_ids = [row[0] for row in repo_values]
    org_repo_names = [row[1] for row in repo_values]

    return org_repo_ids, org_repo_names


@callback(
    [Output("projects", "options")],
    [Input("projects", "search_value")],
    [State("projects", "value")],
)
def dropdown_dynamic_callback(user_in, selections):

    """
    Ref: https://dash.plotly.com/dash-core-components/dropdown#dynamic-options

    For all of the possible repo's / orgs, check if the substring currently
    being searched is in the repo's name or if the repo / org name is
    in the current list of states selected. Add it to the list if it matches
    either of the options.
    """

    if selections is None:
        selections = []

    if user_in is None or len(user_in) == 0:
        raise dash.exceptions.PreventUpdate
    else:
        # match lowercase inputs with lowercase possible values
        opts = [i[1] for i in all_entries if user_in.lower() in i[0]]

        # sort matches by length
        opts.sort(key=lambda item: (len(item), item))

        # always include the previous selections from the searchbar to avoid
        # those values being clobbered when we truncate the total length.
        # arbitrarily 'small' number of matches returned..
        if len(opts) < 250:
            return [opts + selections]
        else:
            return [opts[:250] + selections]


# callback for repo selections to feed into visualization call backs
@callback(
    [Output("results-output-container", "children"), Output("repo-choices", "data")],
    Input("search", "n_clicks"),
    State("projects", "value"),
)
def update_output(n_clicks, value):
    if value is None:
        logging.info("No update")
        return dash.exceptions.PreventUpdate, dash.exceptions.PreventUpdate

    """
    Section handles parsing the input repos / orgs when there is selected values
    """
    logging.debug("SEARCHBAR_ORG_REPO_PARSING - START")
    if len(value) > 0:
        repo_git_set = []
        org_name_set = []

        # split our processing of repos / orgs into two streams
        for r in value:
            if r.startswith("http"):
                repo_git_set.append(r)
            else:
                org_name_set.append(r)

        # get the repo_ids and the repo_names from our repo set of urls'
        repo_ids, repo_names = _parse_repo_choices(repo_git_set=repo_git_set)

        # get the repo_ids and the repo_names from our org set of names
        org_repo_ids, org_repo_names = _parse_org_choices(org_name_set=org_name_set)

        # collect all of the id's and names together
        total_ids = set(repo_ids + org_repo_ids)
        total_names = set(repo_names + org_repo_names)
        total_ids = list(total_ids)

        selections = str(value)

        # return the string that we want and return the list of the id's that we need for the other callback.
        logging.debug("SEARCHBAR_ORG_REPO_PARSING - END")
        logging.debug("=========================================================")
        return f"Your current selections is: {selections[1:-1]}", list(total_ids)
    elif len(value) == 0:
        return dash.exceptions.PreventUpdate, dash.exceptions.PreventUpdate


@callback(Output("help-alert", "is_open"), Input("search-help", "n_clicks"), State("help-alert", "is_open"))
def show_help_alert(n_clicks, openness):
    if n_clicks == 0:
        return dash.no_update
    # switch the openness parameter, allows button to also
    # dismiss the Alert.
    return not openness
