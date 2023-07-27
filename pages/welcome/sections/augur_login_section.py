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
                                html.H1("Logging in to Augur"),
                                html.P(
                                    """
                            There are no 8Knot accounts, exactly.
                            Accounts are created and managed by Augur, and account information is used to enrich the experience
                            of using 8Knot.
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
                                        html.H2("1. Register for an Augur account"),
                                        html.P(
                                            """
                                                After clicking on "Augur log in/sign up" in the top right corner of the page,
                                                you'll be redirected to the Augur frontend where you can create an account.
                                            """
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_card instruction_card_body centered_img",
                                    children=[
                                        html.Img(
                                            className="instruction_image scale_smaller",
                                            src="assets/welcome_login_section/AugurRegister.png",
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
                                        html.H2("2. Authorize 8Knot to access your user preferences"),
                                        html.P(
                                            """
                                                Once you've created your account, you'll be redirected to an
                                                authorization page. This page requests that you allow 8Knot
                                                and Augur to share your account data to enrich your experience.
                                            """
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="instruction_card instruction_card_body centered_img",
                                    children=[
                                        html.Img(
                                            className="instruction_image",
                                            src="assets/welcome_login_section/AugurAuthorize.png",
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
                                        html.H2("3. Successful Login"),
                                        html.P(
                                            """
                                                After authorizing with Augur, new icons should be available,
                                                including a panel with your username.
                                                "Refresh Groups" will update any group changes made in Augur.
                                                "Manage Groups" opens a new Augur tab where you can make changes to your groups.
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
                    ],
                ),
            ],
        ),
    ],
)
