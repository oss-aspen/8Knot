"""
    Profiling stuff
"""
import pstats
import cProfile

"""
    App imports
"""
from dash import html
from dash import dcc
import dash
import dash_labs as dl
import dash_bootstrap_components as dbc
from app import app, entries
import os

# import page files from project.
from pages import start, overview, cicd, chaoss
import index_callbacks 

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
                        html.H1(
                            "Sandiego Explorer Demo Multipage", className="text-center"
                        ),

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
                                            options=[
                                                {"label": x, "value": x}
                                                for x in entries
                                            ],
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
                        html.Div(id="results-output-container", className="mb-4"),
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
                        html.Footer(
                            "Report issues to jkunstle@redhat.com, topic: Explorer Issue",
                            style={"textDecoration": "underline"},
                        )
                    ],
                    width={"offset": 9},
                )
            ],
        ),
    ],
    fluid=True,
    style={"padding-top": "1em"},
)

print("VALIDATE_LAYOUT - START")
app.layout = index_layout

### Assemble all layouts ###
app.validation_layout = html.Div(
    children=[index_layout, start.layout, overview.layout, cicd.layout, chaoss.layout]
)
print("VALIDATE_LAYOUT - END")


def main():
    app.run_server(host="0.0.0.0", port=8050, debug=True)

if __name__ == "__main__":
    try:
        if(os.environ["profiling"] == "True"):
            """
                Ref for how to do this:
                https://www.youtube.com/watch?v=dmnA3axZ3FY

                Credit to IDG TECHTALK
            """
            print("Profiling")

            cProfile.run("main()", "output.dat")

            with open("output_time.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("time").print_stats()

            with open("output_calls.txt", "w") as f:
                p = pstats.Stats("output.dat", stream=f)
                p.sort_stats("calls").print_stats()
    except KeyError:
        print("---------PROFILING OFF---------")
        main()