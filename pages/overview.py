from turtle import title
from dash import html, callback_context, callback, dcc
import plotly.express as px
from dash.dependencies import Input, Output
import plotly
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from app import app
import pandas as pd
import datetime as dt
from .visualizations import commits_activity as ca


layout = dbc.Container(
    [
        dbc.Row([dbc.Col([html.H1(children="Overview Page - live update!")])]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id="commits-over-time"),
                        html.Label(["Date Interval"], style={"font-weight": "bold"}),
                        dcc.RadioItems(
                            id="time-interval",
                            options=[
                                {
                                    "label": "Day",
                                    "value": 86400000,
                                },  # days in milliseconds for ploty use
                                {
                                    "label": "Week",
                                    "value": 604800000,
                                },  # weeks in milliseconds for ploty use
                                {"label": "Month", "value": "M1"},
                                {"label": "Year", "value": "M12"},
                            ],
                            value="M1",
                            style={"width": "50%"},
                        ),
                    ],
                ),
                dbc.Col(
                    [
                        dcc.Graph(id="issues-over-time"),
                    ],
                ),
            ]
        ),
    ],
    fluid=True,
)

# callback for commits over time graph
@callback(
    Output("commits-over-time", "figure"),
    [Input("commits-data", "data"), Input("time-interval", "value")],
)
def create_graph(data, interval):
    df_commits = pd.DataFrame(data)

    # reset index to be ready for plotly
    df_commits = df_commits.reset_index()

    # helper values for building graph
    today = dt.date.today()
    x_r = []
    x_name = "Year"
    hover = "Year: %{x|%Y}"

    # graph input values based on date interval selection
    if interval == 86400000:  # if statement for days
        x_r = [str(today - dt.timedelta(weeks=4)), str(today)]
        x_name = "Day"
        hover = "Day: %{x|%b %d, %Y}"
    elif interval == 604800000:  # if statmement for weeks
        x_r = [str(today - dt.timedelta(weeks=30)), str(today)]
        x_name = "Week"
        hover = "Week: %{x|%b %d, %Y}"
    elif interval == "M1":  # if statement for months
        x_r = [str(today - dt.timedelta(weeks=104)), str(today)]
        x_name = "Month"
        hover = "Month: %{x|%b %Y}"

    # graph geration
    if df_commits is not None:
        fig = px.histogram(
            df_commits, x="date", range_x=x_r, labels={"x": x_name, "y": "Commits"}
        )
        fig.update_traces(
            xbins_size=interval, hovertemplate=hover + "<br>Commits: %{y}<br>"
        )
        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=interval,
            rangeslider_yaxis_rangemode="match",
        )
        fig.update_layout(
            title={
                "text": "Commits Over Time",
                "font": {"size": 28},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title=x_name,
            yaxis_title="Number of Commits",
        )
        return fig
    else:
        return None


# callback for issues over time graph
@callback(
    Output("issues-over-time", "figure"),
    [Input("issues-data", "data"), Input("time-interval", "value")],
)
def create_graph(data, interval):
    df_issues = pd.DataFrame(data)

    # df for line chart
    df_open = make_open_df(df_issues)

    # reset index to be ready for plotly
    df_issues = df_issues.reset_index()

    # helper values for building graph
    today = dt.date.today()
    x_r = None
    x_name = "Year"
    hover = "Year: %{x|%Y}"

    # graph input values based on date interval selection
    if interval == 86400000:
        x_r = [str(today - dt.timedelta(weeks=4)), str(today)]
        x_name = "Day"
        hover = "Day: %{x|%b %d, %Y}"
    elif interval == 604800000:
        x_r = [str(today - dt.timedelta(weeks=30)), str(today)]
        x_name = "Week"
        hover = "Week: %{x|%b %d, %Y}"
    elif interval == "M1":
        x_r = [str(today - dt.timedelta(weeks=104)), str(today)]
        x_name = "Month"
        hover = "Month: %{x|%b %Y}"

    # graph geration
    if df_issues is not None:
        fig = go.Figure()
        fig.add_histogram(
            x=df_issues["closed"].dropna(),
            histfunc="count",
            name="closed",
            opacity=1,
            hovertemplate=hover + "<br>Closed: %{y}<br>" + "<extra></extra>",
        )
        fig.add_histogram(
            x=df_issues["created"],
            histfunc="count",
            name="created",
            opacity=0.6,
            hovertemplate=hover + "<br>Created: %{y}<br>" + "<extra></extra>",
        )
        fig.update_traces(xbins_size=interval)
        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=interval,
            rangeslider_yaxis_rangemode="match",
            range=x_r,
        )
        fig.update_layout(
            title={
                "text": "Issues Over Time",
                "font": {"size": 28},
                "x": 0.5,
                "xanchor": "center",
            },
            xaxis_title=x_name,
            yaxis_title="Number of Issues",
            barmode="overlay",
        )
        fig.add_trace(
            go.Scatter(
                x=df_open["issue"],
                y=df_open["total"],
                mode="lines",
                name="Issues Actively Open",
                hovertemplate="Issues Open: %{y}" + "<extra></extra>",
            )
        )
        return fig
    else:
        return None


def make_open_df(df_issues):
    # created dataframe
    df_created = pd.DataFrame(df_issues["created"])
    df_created.rename(columns={"created": "issue"}, inplace=True)
    df_created["open"] = 1

    # closed dataframe
    df_closed = pd.DataFrame(df_issues["closed"]).dropna()
    df_closed.rename(columns={"closed": "issue"}, inplace=True)
    df_closed["open"] = -1

    # sum created and closed value to get actively open issues dataframe

    df_open = pd.concat([df_created, df_closed])
    df_open = df_open.sort_values("issue")
    df_open = df_open.reset_index(drop=True)
    df_open["total"] = df_open["open"].cumsum()
    df_open["issue"] = pd.to_datetime(df_open["issue"])
    df_open["issue"] = df_open["issue"].dt.floor("D")
    df_open = df_open.drop_duplicates(subset="issue", keep="last")
    df_open = df_open.drop(columns="open")
    return df_open
