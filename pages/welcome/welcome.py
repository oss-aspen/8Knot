from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import plotly.express as px

# import other sections
from .sections.general_section import layout as general_tab_contents
from .sections.plotly_section import layout as plotly_tab_contents
from .sections.augur_login_section import layout as augur_tab_contents

# register the page
dash.register_page(__name__, path="/", order=1)


layout = dbc.Container(
    className="welcome_container",
    children=[
        html.Div(
            className="toplevel_welcome_div",
            children=[
                html.Div(
                    className="welcome_callout_section",
                    children=[
                        html.Img(src="assets/logo-color.png"),
                        html.P(
                            """
                            8Knot hosts advanced analysis of open source projects, enriching
                            the study of communities for community architects, developers,
                            and Business Intelligence experts alike.
                            """
                        ),
                    ],
                ),
                html.Div(
                    className="welcome_instructions_section",
                    children=[
                        dcc.Tabs(
                            value="general",
                            children=[
                                dcc.Tab(
                                    label="General",
                                    value="general",
                                    children=[general_tab_contents],
                                ),
                                dcc.Tab(
                                    label="Plotly Figure Tools",
                                    value="plotlyfiguretools",
                                    children=[plotly_tab_contents],
                                ),
                                dcc.Tab(
                                    label="Your Augur Account",
                                    value="auguraccount",
                                    children=[augur_tab_contents],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
    ],
)
