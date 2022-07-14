from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
import logging
import plotly.express as px
from utils.graph_utils import get_graph_time_values

gc_total_contributor_growth = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(
                    id="overview-graph-title-1",
                    className="card-title",
                    style={"text-align": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Information on graph 1"),
                    ],
                    id="overview-popover-1",
                    target="overview-popover-target-1",  # needs to be the same as dbc.Button id
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    children=[dcc.Graph(id="total_contributor_growth")],
                    color="#119DFF",
                    type="dot",
                    fullscreen=False,
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval",
                                    html_for="contributor-growth-time-interval",
                                    width="auto",
                                    style={"font-weight": "bold"},
                                ),
                                dbc.Col(
                                    dbc.RadioItems(
                                        id="contributor-growth-time-interval",
                                        options=[
                                            {
                                                "label": "Trend",
                                                "value": -1,
                                            },
                                            {
                                                "label": "Day",
                                                "value": "D1",
                                            },
                                            {"label": "Month", "value": "M1"},
                                            {"label": "Year", "value": "M12"},
                                        ],
                                        value="M1",
                                        inline=True,
                                    ),
                                    className="me-2",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id="overview-popover-target-1",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"padding-top": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        ),
    ],
    color="light",
)


# call backs for card graph 1 - total contributor growth
@callback(
    Output("overview-popover-1", "is_open"),
    [Input("overview-popover-target-1", "n_clicks")],
    [State("overview-popover-1", "is_open")],
)
def toggle_popover_1(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("overview-graph-title-1", "children"),
    Input("contributor-growth-time-interval", "value"),
)
def graph_title(view):
    title = ""
    if view == -1:
        title = "Total Contributors Over Time"
    elif view == "D1":
        title = "New Contributors by Day"
    elif view == "M1":
        title = "New Contributors by Month"
    else:
        title = "New Contributors by Year"
    return title


@callback(
    Output("total_contributor_growth", "figure"),
    [
        Input("contributions", "data"),
        Input("contributor-growth-time-interval", "value"),
    ],
)
def create_total_contributor_growth_graph(data, bin_size):
    logging.debug("TOTAL_CONTRIBUTOR_GROWTH_VIZ - START")
    df_contrib = pd.DataFrame(data)

    """
        Assume that the cntrb_id values are unique to individual contributors.
        Find the first rank-1 contribution of the contributors, saving the created_at
        date.
    """

    # keep only first contributions
    df_contrib = df_contrib[df_contrib["rank"] == 1]

    # order from beginning of time to most recent
    df_contrib = df_contrib.sort_values("created_at", axis=0, ascending=True)

    # convert to datetime objects rather than strings, add day column
    df_contrib["created_at"] = pd.to_datetime(df_contrib["created_at"], utc=True)

    # get all of the unique entries by contributor ID
    df_contrib = df_contrib.drop_duplicates(subset=["cntrb_id"])

    if bin_size == -1:
        fig = contributor_growth_line_bar(df_contrib)
    else:
        fig = contributor_growth_bar_graph(df_contrib, bin_size)

    logging.debug("TOTAL_CONTRIBUTOR_GROWTH_VIZ - END")
    # return the simple line graph
    return fig


def contributor_growth_bar_graph(df_contrib, bin_size):

    """
    Group-by determined by the radio button options.
    Aggregation is the number of rows per time bin.
    Days, Months, Years are all options.
    """
    if bin_size == "D1":
        group = df_contrib.groupby(pd.Grouper(key="created_at", axis=0, freq="1D")).size()
    elif bin_size == "M1":
        group = df_contrib.groupby(pd.Grouper(key="created_at", axis=0, freq="1M")).size()
    else:
        group = df_contrib.groupby(pd.Grouper(key="created_at", axis=0, freq="1Y")).size()

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(bin_size)

    # reset index from group-by aggregation step
    group = group.reset_index()
    # rename the columns for clarity
    group = group.rename(columns={"created_at": "date", 0: "count"})

    # correction for year binning -
    # rounded up to next year so this is a simple patch
    if bin_size == "M12":
        group["date"] = group["date"].dt.year

    # create the graph
    fig = px.bar(group, x="date", y="count", range_x=x_r, labels={"x": x_name, "y": "Contributors"})

    # edit hover values
    fig.update_traces(hovertemplate=hover + "<br>Contributors: %{y}<br>")

    # make the bars thicker for further-spaced values
    # so that we can see the per-day increases clearly.
    # fig.update_traces(marker_color="blue", marker_line_color="blue", selector=dict(type="bar"))

    # add the date-range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )

    # label the figure correctly.
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Contributors",
        margin_r=20,
    )
    return fig


def contributor_growth_line_bar(df_contrib):

    # reset index to enumerate contributions
    df_contrib = df_contrib.reset_index()
    df_contrib = df_contrib.drop(["index"], axis=1)
    df_contrib = df_contrib.reset_index()

    # create the figure
    fig = px.line(
        df_contrib,
        x="created_at",
        y="index",
    )

    # edit hover values
    fig.update_traces(hovertemplate="%{x}" + "<br>Contributors: %{y}<br>")

    """
        Ref. for this awesome button thing:
        https://plotly.com/python/range-slider/
    """
    # add the date-range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )

    # label the figure correctly
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Contributors",
        margin_b=40,
        margin_r=20,
    )
    return fig
