from dash import html, dcc, Input, State, Output, callback
import dash_bootstrap_components as dbc


# All-in-One Components should be suffixed with 'AIO'
class VisualizationAIO(dbc.Card):
    def __init__(self, page: str, viz_id: str, graph_info="", class_name="", controls=None):
        """
        Common visualization shell to be shared by all visualizations

        Args:
            page (str): The name of the page this visualization is part of
            viz_id (str): a unique id for this visualization
            graph_info (str): The description of this graph giving more information on what it describes and where its data came from. Displayed in a popover.
            class_name (str): Any custom class names to associate with this card
            controls (list): A list of form elements to display within the lower form Row at the bottom of the graph
        """
        self.page = page
        self.viz_id = viz_id

        if controls is None:
            controls = []

        # Define the component's layout
        super().__init__(
            [
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(html.H3(id=f"graph-title-{page}-{viz_id}", className="card-title")),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"popover-target-{page}-{viz_id}",
                                        color="outline-secondary",
                                        size="sm",
                                        className="about-graph-button",
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
                            id=f"popover-{page}-{viz_id}",
                            target=f"popover-target-{page}-{viz_id}",
                            placement="top",
                            is_open=False,
                        ),
                        dcc.Loading(
                            dcc.Graph(id=f"{page}-{viz_id}"),
                            style={"marginBottom": "1rem"},
                        ),
                        html.Hr(className="card-split"),  # Divider between graph and controls
                        dbc.Form(
                            [
                                dbc.Row(
                                    controls,
                                    align="center",
                                    justify="start",
                                ),
                            ]
                        ),
                    ],
                    style={"padding": "1.5rem"},
                ),
            ],
            className=class_name,
        )

    # callback for graph info popover
    @callback(
        Output(f"popover-{self.page}-{self.viz_id}", "is_open"),
        [Input(f"popover-target-{self.page}-{self.viz_id}", "n_clicks")],
        [State(f"popover-{self.page}-{self.viz_id}", "is_open")],
    )
    def toggle_popover(n, is_open):
        if n:
            return not is_open
        return is_open
