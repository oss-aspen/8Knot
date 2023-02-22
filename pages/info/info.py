from dash import dcc
import dash
import dash_bootstrap_components as dbc

# register the page
dash.register_page(__name__, path="/info", order=4)

layout = dbc.Container(
    [
        dcc.Markdown(
            """

            ### Defintions
            -------
            __Contribution__
                > Definition for item here.

            __Contributor__
                > Definition for item here.

            __Active Contributor__
                > Definition for item here.

            __Drifting Contributor__
                > Definition for item here.

            __Fly-By Contributor__
                > Definition for item here.

            __Repeat Contributor__
                > Definition for item here.

            __Staleness__
                > Definition for item here.

            *__Note:__ These definitions are specifically for the data that is being used to populate this graph. It is not indictive of the
            overall philosophy on open source communities.*

            ### Page Community Health Lens
            -------
            Explaination of the grouping of visualizations on each page

            ### Plotly Graph Functionality
            -------

            Plotly graphs have a mode bar if you hover over the top of the title.

            If you want to reset the view of a graph with customization options, toggle one of the options to reset the view.


        """
        )
    ],
    fluid=True,
)
