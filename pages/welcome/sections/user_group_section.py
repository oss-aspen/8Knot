from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

layout = html.Div(
    className="tab_section_container",
    children=[
        html.Div(
            className="card_section_container",
            children=[
                html.Div(
                    className="card_section_container_centered",
                    children=[
                        html.Div(
                            className="card_section_description",
                            children=[
                                html.H1("Adding a User Group"),
                                html.P(
                                    """
                            User groups are customizable groups of organization or repositories that are accessible each time you
                            log in. Adding repositories and organizations to a user group also triggers collection if they are not
                            already populated in Augur. These intructions assume you are logged in to your Augur account.
                            """
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="card_section_body card_section_body_vertical",
                    children=[
                        html.Div(
                            className="instruction_card instruction_card_split",
                            children=[
                                html.Div(
                                    className="instruction_card instruction_card_body",
                                    children=[
                                        html.H2("1. Click Manage Groups"),
                                        html.P(
                                            """
                                                After clicking on "Manage Groups" in the top right corner of the page,
                                                you'll be redirected to the Augur frontend where you can see your User Groups.
                                            """
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_card instruction_card_body centered_img",
                                    children=[
                                        html.Img(
                                            className="instruction_image scale_smaller",
                                            src="assets/welcome_login_section/8KnotLoggedIn.png",
                                        )
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="instruction_card instruction_card_split",
                            children=[
                                html.Div(
                                    className="instruction_card instruction_card_body",
                                    children=[
                                        html.H2("2. Add New Group Name"),
                                        html.P(
                                            """
                                                To start creating a new user group, you need to type in the name
                                                and click "add" .
                                            """
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_card instruction_card_body centered_img",
                                    children=[
                                        html.Img(
                                            className="instruction_image",
                                            src="assets/welcome_user_group_section/new_group_name.png",
                                        )
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="instruction_card instruction_card_split",
                            children=[
                                html.Div(
                                    className="instruction_card instruction_card_body",
                                    children=[
                                        html.H2("3. Add Repositories and Organizations"),
                                        html.P(
                                            """
                                                Once you add your new group, you can now select it in the "group
                                                name" dropdown. Once selected, now add the repositories and organizations
                                                you want in your group and click "add". Note: if the repository or organization
                                                does not already exist in the database, adding it to a group will trigger
                                                collection but will not automatically show up in 8Knot. To check if the repository
                                                does not already exist in Augur, it will show as all "0s" in the Augur front end.
                                            """
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_card instruction_card_body centered_img",
                                    children=[
                                        html.Img(
                                            className="instruction_image",
                                            src="assets/welcome_user_group_section/add_repos.png",
                                        )
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="instruction_card instruction_card_split",
                            children=[
                                html.Div(
                                    className="instruction_card instruction_card_body",
                                    children=[
                                        html.H2("4. Click Refresh Groups"),
                                        html.P(
                                            """
                                                Once you have created or edited your groups, go back to the 8Knot front end and click
                                                "Refresh Groups" to be able to be able to search for your group in the 8Knot
                                                front end. Note: if any of the repositories are new to the database they will not
                                                be included in the group until collection finishes.
                                            """
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_card instruction_card_body centered_img",
                                    children=[
                                        html.Img(
                                            className="instruction_image",
                                            src="assets/welcome_login_section/8KnotLoggedIn.png",
                                        )
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className="instruction_card instruction_card_split",
                            children=[
                                html.Div(
                                    className="instruction_card instruction_card_body",
                                    children=[
                                        html.H2("5. Search User Groups"),
                                        html.P(
                                            """
                                                Once you have refreshed, you can now search for your user groups by
                                                typing in your username and the groups will populate.
                                            """
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_card instruction_card_body centered_img",
                                    children=[
                                        html.Img(
                                            className="instruction_image",
                                            src="assets/welcome_user_group_section/group_search.png",
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
