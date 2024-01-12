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
                                html.H1("8Knot Pages"),
                                html.P(
                                    """
                                    Each page approaches the study of open source communities from a different perspective.
                                    """
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="card_section_body",
                    children=[
                        html.Div(
                            className="info_card",
                            children=[
                                html.H2("Repo Overview"),
                                html.P(
                                    """
                                    General information at the repo group and single repo level
                                   """
                                ),
                            ],
                        ),
                        html.Div(
                            className="info_card",
                            children=[
                                html.H2("Contributions"),
                                html.P(
                                    """
                                    Track large community trends over time based on contribution types
                                   """
                                ),
                            ],
                        ),
                        html.Div(
                            className="info_card",
                            children=[
                                html.H2("Contributors"),
                                html.P(
                                    """
                                    Track trends based on contributors, broken down by behavior and contribution types
                                   """
                                ),
                            ],
                        ),
                        html.Div(
                            className="info_card",
                            children=[
                                html.H2("CHAOSS"),
                                html.P("Advanced metrics defined and refined by the CHAOSS project"),
                            ],
                        ),
                        html.Div(
                            className="info_card",
                            children=[
                                html.H2("Affiliation"),
                                html.P(
                                    "Summarize likely company and institution affiliation with contributor behavior"
                                ),
                            ],
                        ),
                        html.Div(
                            className="info_card",
                            children=[
                                html.H2("Info"),
                                html.P("Information about visualizations and definitions of any terms used"),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            # has no distinct header, so set container to be flex conatiner
            className="card_section_container card_section_body architecture_section",
            children=[
                html.Div(
                    className="architecture_description architecture_section_part",
                    children=[
                        html.H1("How 8Knot works"),
                        html.P(
                            """
                        8Knot is a data analytics application that uses data from Augur
                        to render visualizations and generate metrics.
                    """
                        ),
                        html.H2("Cloud-native architecture"),
                        html.P(
                            """
                        We designed 8Knot to be easily deployable locally, but to also scale
                        well in the cloud. On a laptop it's a multi-container application. On
                        a container orchestration platform (Openshift, Kubernetes) it's multi-service.
                    """
                        ),
                        html.H2("Data science first"),
                        html.P(
                            """
                        All analytical processing is done with Python data science packages. If a
                        workload is sufficiently complex, we can use distributed computing to handle
                        it. Machine learning and modeling are first-priority workloads.
                        """
                        ),
                    ],
                ),
                html.Img(
                    className="architecture_image architecture_section_part",
                    src="assets/8KnotArch.png",
                ),
            ],
        ),
    ],
)
