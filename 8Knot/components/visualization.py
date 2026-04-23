import dash
from dash import html, dcc, Input, State, Output, callback, MATCH
import dash_bootstrap_components as dbc
from typing import Optional


# All-in-One Components should be suffixed with 'AIO'
class VisualizationAIO(dbc.Card):
    def __init__(
        self,
        page: str,
        viz_id: str,
        graph_info="",
        class_name="",
        controls=None,
        title: str = "",
        id: Optional[str] = None,
    ):
        """
        Common visualization shell to be shared by all visualizations

        Args:
            page (str): The name of the page this visualization is part of
            viz_id (str): a unique id for this visualization
            graph_info (str): The description of this graph giving more information on what it describes and where its data came from. Displayed in a popover.
            class_name (str): Any custom class names to associate with this card
            controls (list): A list of form elements to display within the lower form Row at the bottom of the graph
            title (Optional[str]): a static title. If none, the title will be fetched from a callback with the id "graph-title-{page}-{viz_id}". Defaults to none.
            id (Optional[str]): an identifier to use to jump to the card. Primarily intended for navigation, not for styling. Defaults to none, which causes {page}-{viz_id} to be used
        """
        self.page = page
        self.viz_id = viz_id
        self.nav_id = id

        if controls is None:
            controls = []

        # The card anchor is what the sidebar nav links point to.
        # We reuse it as the pattern-matching index for the copy-link button
        # so the JS can construct the correct #anchor URL fragment.
        anchor = id if id is not None else f"{page}-{viz_id}"

        # Define the component's layout
        super().__init__(
            [
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.H3(title, id=f"graph-title-{page}-{viz_id}", className="card-title")),
                                # Right-side button group: copy-link + About Graph
                                dbc.Col(
                                    html.Div(
                                        [
                                            # Copy-link button — copies a URL with #anchor appended
                                            dbc.Button(
                                                html.I(className="fas fa-link"),
                                                id={"type": "copy-link-btn", "index": anchor},
                                                color="link",
                                                size="sm",
                                                title="Copy link to this graph",
                                                className="about-graph-button",
                                                n_clicks=0,
                                            ),
                                            dbc.Tooltip(
                                                "Link copied!",
                                                target={"type": "copy-link-btn", "index": anchor},
                                                trigger="click",
                                                placement="top",
                                            ),
                                            # Hidden output sink for the clientside clipboard callback
                                            html.Div(
                                                id={"type": "copy-link-sink", "index": anchor},
                                                style={"display": "none"},
                                            ),
                                            dbc.Button(
                                                "About Graph",
                                                id={"type": "popover-target", "index": f"{page}-{viz_id}"},
                                                color="outline-secondary",
                                                size="sm",
                                                className="about-graph-button",
                                            ),
                                        ],
                                        className="d-flex align-items-center gap-1",
                                    ),
                                    width="auto",
                                ),
                            ],
                            align="center",
                            justify="between",
                            className="mb-3",
                        ),
                        dbc.Popover(
                            [
                                dbc.PopoverHeader("Graph Info:"),
                                dbc.PopoverBody(graph_info),
                            ],
                            id={"type": "popover", "index": f"{page}-{viz_id}"},
                            target={"type": "popover-target", "index": f"{page}-{viz_id}"},
                            placement="top",
                            is_open=False,
                        ),
                        dcc.Loading(
                            dcc.Graph(id=f"{page}-{viz_id}"),
                            style={"marginBottom": "1rem"},
                        ),
                        html.Hr(className="card-split") if controls else None,  # Divider between graph and controls
                        (
                            dbc.Form(
                                [
                                    dbc.Row(
                                        controls,
                                        align="center",
                                        justify="start",
                                    ),
                                ]
                            )
                            if controls
                            else None
                        ),
                    ],
                    style={"padding": "1.5rem"},
                ),
            ],
            className=class_name,
            id=(self.nav_id if self.nav_id is not None else f"{self.page}-{self.viz_id}"),
        )

    # callback for graph info popover
    @callback(
        Output({"type": "popover", "index": MATCH}, "is_open"),
        [Input({"type": "popover-target", "index": MATCH}, "n_clicks")],
        [State({"type": "popover", "index": MATCH}, "is_open")],
    )
    def toggle_popover(n, is_open):
        if n:
            return not is_open
        return is_open


# =============================================================================
# Per-graph copy-link — clientside clipboard write
#
# Registered once at module level using MATCH so it covers every
# VisualizationAIO card without repeating callback code.
#
# The button's pattern-matching index IS the card's anchor id (e.g.
# "commits-over-time"). The JS implementation is in assets/copy_link.js
# for better maintainability, linting, and separation of concerns.
#
# The JS function builds: origin + pathname + search + "#" + anchor
# so the copied URL points directly to this graph with the current
# repo selection already encoded in the query string.
# =============================================================================

dash.clientside_callback(
    dash.ClientsideFunction(
        namespace="clientside",
        function_name="copy_link_to_clipboard",
    ),
    Output({"type": "copy-link-sink", "index": MATCH}, "children"),
    Input({"type": "copy-link-btn", "index": MATCH}, "n_clicks"),
    State({"type": "copy-link-btn", "index": MATCH}, "id"),
    prevent_initial_call=True,
)
