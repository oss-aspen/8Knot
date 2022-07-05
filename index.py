"""
    README -- Organization of Callback Functions

    In an effort to compartmentalize our development where possible, all callbacks directly relating
    to pages in our application are in their own files.

    For instance, this file contains the layout logic for the index page of our app-
    this page serves all other paths by providing the searchbar, page routing faculties,
    and data storage objects that the other pages in our app use.

    Having laid out the HTML-like organization of this page, we write the callbacks for this page in
    the neighbor 'index_callbacks.py' file.
"""
import pstats
import cProfile

from dash import html
from dash import dcc
import dash
import dash_labs as dl
import dash_bootstrap_components as dbc
from app import app, entries
import os
import logging

# import page files from project.
from pages import start, overview, cicd, chaoss
import index_callbacks


# side bar code for page navigation
sidebar = html.Div(
    [
        html.H2("Pages", className="display-10"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(page["name"], href=page["path"])
                for page in dash.page_registry.values()
                if page["module"] != "pages.not_found_404"
            ],
            vertical=True,
            pills=True,
        ),
    ]
)

# summary layout of the page
index_layout = dbc.Container(
    [
        # componets to store data from queries
        dcc.Store(id="repo_choices", storage_type="session", data=[]),
        dcc.Store(id="commits-data", data=[], storage_type="memory"),
        dcc.Store(id="contributions", data=[], storage_type="memory"),
        dcc.Store(id="issues-data", data=[], storage_type="memory"),
        dcc.Location(id="url"),
        dbc.Row(
            [
                # from above definition
                dbc.Col(sidebar, width=1),
                dbc.Col(
                    [
                        html.H1("Sandiego Explorer Demo Multipage", className="text-center"),
                        # search bar with buttons
                        html.Label(
                            ["Select Github repos or orgs:"],
                            style={"font-weight": "bold"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Dropdown(
                                            id="projects",
                                            multi=True,
                                            value=["agroal"],
                                            options=["agroal"],
                                        )
                                    ],
                                    style={
                                        "width": "50%",
                                        "display": "table-cell",
                                        "verticalAlign": "middle",
                                        "padding-right": "10px",
                                    },
                                ),
                                dbc.Button(
                                    "Search",
                                    id="search",
                                    n_clicks=0,
                                    class_name="btn btn-primary",
                                    style={
                                        "verticalAlign": "top",
                                        "display": "table-cell",
                                    },
                                ),
                            ],
                            style={
                                "align": "right",
                                "display": "table",
                                "width": "60%",
                            },
                        ),
                        dcc.Loading(
                            children=[html.Div(id="results-output-container", className="mb-4")],
                            color="#119DFF",
                            type="dot",
                            fullscreen=True,
                        ),
                        # where our page will be rendered
                        dl.plugins.page_container,
                    ],
                    width={"size": 11},
                ),
            ],
            justify="start",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5(
                            "Have a bug or feature request?",
                            className="mb-2"
                            # style={"textDecoration": "underline"},
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "Visualization request",
                                    color="primary",
                                    className="me-1",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=enhancement%2Cvisualization&template=visualizations.md",
                                ),
                                dbc.Button(
                                    "Bug",
                                    color="primary",
                                    className="me-1",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=bug&template=bug_report.md",
                                ),
                                dbc.Button(
                                    "Repo/Org Request",
                                    color="primary",
                                    external_link=True,
                                    target="_blank",
                                    href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=augur&template=augur_load.md",
                                ),
                            ]
                        ),
                    ],
                    width={"offset": 10},
                )
            ],
        ),
    ],
    fluid=True,
    className="dbc",
    style={"padding-top": "1em"},
)

logging.debug("VALIDATE_LAYOUT - START")
app.layout = index_layout

### Assemble all layouts ###
app.validation_layout = html.Div(children=[index_layout, start.layout, overview.layout, cicd.layout, chaoss.layout])
logging.debug("VALIDATE_LAYOUT - END")


def main():

    # shouldn't run server in debug mode if we're in a production setting

    debug_mode = True
    try:
        if os.environ["running_on"] == "prod":
            debug_mode = False
        else:
            debug_mode = True
    except:
        debug_mode = True

    app.run_server(host="0.0.0.0", port=8050, debug=debug_mode)


if __name__ == "__main__":
    try:
        if os.environ["profiling"] == "True":
            """
            Ref for how to do this:
            https://www.youtube.com/watch?v=dmnA3axZ3FY

            Credit to IDG TECHTALK
            """
            logging.debug("Profiling")

            cProfile.run("main()", "output.dat")

            with open("output_time.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("time").print_stats()

            with open("output_calls.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("calls").print_stats()
    except KeyError:
        logging.debug("---------PROFILING OFF---------")
        main()
