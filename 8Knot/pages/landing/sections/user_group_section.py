from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

layout = html.Div(
    className="figma-content-container",
    children=[
        # Summary Section
        html.Div(
            className="figma-summary",
            children=[
                # Main title
                html.Div(
                    className="figma-main-title",
                    children=[
                        html.H1("Creating Group Projects"),
                    ],
                ),
                # Section 1 Body
                html.Div(
                    className="figma-section-body",
                    children=[
                        html.Div(
                            className="figma-body-text",
                            children=[
                                html.P(
                                    "User groups are customizable groups of organization or repositories that are accessible each time you log in. Adding repositories and organizations to a user group also triggers collection if they are not already populated in Augur. These instructions assume you are logged in to your Augur account."
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        # Section 2 - Bordered Content
        html.Div(
            className="figma-section-bordered",
            children=[
                # Step 1 - Click Manage Groups
                html.Div(
                    className="figma-feature-section",
                    children=[
                        html.Div(
                            className="figma-feature-title",
                            children=[
                                html.Div(
                                    className="figma-section-title",
                                    children=[
                                        html.H3("1. Click Manage Groups"),
                                    ],
                                ),
                                html.Div(
                                    className="figma-feature-body",
                                    children=[
                                        html.P(
                                            'After clicking on "Manage Groups" in the top right corner of the page, you\'ll be redirected to the Augur frontend where you can see your User Groups.'
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="figma-gif-container",
                            children=[
                                html.Img(
                                    className="figma-gif-image",
                                    src="assets/welcome_login_section/8KnotLoggedIn.png",
                                ),
                                html.P(
                                    "8Knot Interface with Manage Groups",
                                    className="figma-gif-caption",
                                ),
                            ],
                        ),
                    ],
                ),
                # Step 2 - Add New Group Name
                html.Div(
                    className="figma-feature-section",
                    children=[
                        html.Div(
                            className="figma-feature-title",
                            children=[
                                html.Div(
                                    className="figma-section-title",
                                    children=[
                                        html.H3("2. Add New Group Name"),
                                    ],
                                ),
                                html.Div(
                                    className="figma-feature-body",
                                    children=[
                                        html.P(
                                            'To start creating a new user group, you need to type in the name and click "add".'
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="figma-gif-container",
                            children=[
                                html.Img(
                                    className="figma-gif-image",
                                    src="assets/welcome_user_group_section/new_group_name.png",
                                ),
                                html.P(
                                    "Adding a New Group Name",
                                    className="figma-gif-caption",
                                ),
                            ],
                        ),
                    ],
                ),
                # Step 3 - Add Repositories
                html.Div(
                    className="figma-feature-section",
                    children=[
                        html.Div(
                            className="figma-feature-title",
                            children=[
                                html.Div(
                                    className="figma-section-title",
                                    children=[
                                        html.H3("3. Add Repositories"),
                                    ],
                                ),
                                html.Div(
                                    className="figma-feature-body",
                                    children=[
                                        html.P(
                                            'Once you add your new group, you can now select it in the "group name" dropdown. Once selected, now add the repositories and organizations you want in your group and click "add". Note: if the repository or organization does not already exist in the database, adding it to a group will trigger collection but will not automatically show up in 8Knot.'
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="figma-gif-container",
                            children=[
                                html.Img(
                                    className="figma-gif-image",
                                    src="assets/welcome_user_group_section/add_repos.png",
                                ),
                                html.P(
                                    "Adding Repositories to Group",
                                    className="figma-gif-caption",
                                ),
                            ],
                        ),
                    ],
                ),
                # Step 4 - Refresh Groups
                html.Div(
                    className="figma-feature-section",
                    children=[
                        html.Div(
                            className="figma-feature-title",
                            children=[
                                html.Div(
                                    className="figma-section-title",
                                    children=[
                                        html.H3("4. Refresh Groups"),
                                    ],
                                ),
                                html.Div(
                                    className="figma-feature-body",
                                    children=[
                                        html.P(
                                            'Once you have created or edited your groups, go back to the 8Knot front end and click "Refresh Groups" to be able to search for your group in the 8Knot front end. Note: if any of the repositories are new to the database they will not be included in the group until collection finishes.'
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                # Step 5 - Search User Groups
                html.Div(
                    className="figma-feature-section",
                    children=[
                        html.Div(
                            className="figma-feature-title",
                            children=[
                                html.Div(
                                    className="figma-section-title",
                                    children=[
                                        html.H3("5. Search User Groups"),
                                    ],
                                ),
                                html.Div(
                                    className="figma-feature-body",
                                    children=[
                                        html.P(
                                            "Once you have refreshed, you can now search for your user groups by typing in your username and the groups will populate."
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="figma-gif-container",
                            children=[
                                html.Img(
                                    className="figma-gif-image",
                                    src="assets/welcome_user_group_section/group_search.png",
                                ),
                                html.P(
                                    "Searching for User Groups",
                                    className="figma-gif-caption",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
