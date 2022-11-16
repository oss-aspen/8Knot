import plotly.graph_objects as go

columns = ["1", "2", "3"]

# graph displayed if no data is available
nodata_graph = go.Figure([go.Bar(x=columns, y=[20, 14, 23])])
nodata_graph.update_traces(
    marker_color="rgb(230,230,230)",
    marker_line_color="rgb(200,200,300)",
    marker_line_width=1.5,
    opacity=0.6,
)
nodata_graph.update_layout(
    title={
        "text": "No Available Data",
        "y": 0.9,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
    },
    font=dict(size=18, color="red"),
)

# graph displayed if a worker fails
timeout_graph = go.Figure([go.Bar(x=columns, y=[20, 14, 23])])
timeout_graph.update_traces(
    marker_color="rgb(230,230,230)",
    marker_line_color="rgb(200,200,300)",
    marker_line_width=1.5,
    opacity=0.6,
)
timeout_graph.update_layout(
    title={
        "text": "No Available Data",
        "y": 0.9,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
    },
    font=dict(size=18, color="orange"),
)
