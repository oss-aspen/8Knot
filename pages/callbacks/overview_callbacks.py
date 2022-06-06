import dash
import datetime
from dash import callback
import plotly.express as px
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import datetime as dt

#call backs for card graph 1 - total contributor growth 
@callback(
    Output("overview-popover-1", "is_open"),
    [Input("overview-popover-target-1", "n_clicks")],
    [State("overview-popover-1", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    Output('overview-graph-title-1','children'),
    Input("contributor-growth-time-interval", "value")
)
def graph_title(view):
    title = ""
    if view == -1:
        title = "Total Contributors over Time"
    elif view == "D1":
        title = "New Contributors by Day"
    elif view == "M1":
        title = "New Contributors by Month"
    else: 
        title = "New Contributors by Year"
    return title

#call backs for card graph 2 - Commits Over Time
@callback(
    Output("overview-popover-2", "is_open"),
    [Input("overview-popover-target-2", "n_clicks")],
    [State("overview-popover-2", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

#call backs for card graph 3 - Issue Over Time
@callback(
    Output("overview-popover-3", "is_open"),
    [Input("overview-popover-target-3", "n_clicks")],
    [State("overview-popover-3", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

# callback for commits over time graph
@callback(
    Output("commits-over-time", "figure"),
    [Input("commits-data", "data"), Input("commits-time-interval", "value")],
)
def create_graph(data, interval):
    print("COMMITS_OVER_TIME_VIZ - START")
    df_commits = pd.DataFrame(data)

    # reset index to be ready for plotly
    df_commits = df_commits.reset_index()

    # time values for graph
    x_r, x_name, hover = get_graph_time_values(interval)

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
            xaxis_title=x_name,
            yaxis_title="Number of Commits",
        )
        print("COMMITS_OVER_TIME_VIZ - END")
        return fig
    else:
        return None


# callback for issues over time graph
@callback(
    Output("issues-over-time", "figure"),
    [Input("issues-data", "data"), Input("issue-time-interval", "value")],
)
def create_graph(data, interval):
    print("ISSUES_OVER_TIME_VIZ - START")
    df_issues = pd.DataFrame(data)

    # df for line chart
    df_open = make_open_df(df_issues)

    # reset index to be ready for plotly
    df_issues = df_issues.reset_index()

    # time values for graph
    x_r, x_name, hover = get_graph_time_values(interval)

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
        print("ISSUES_OVER_TIME_VIZ - END")
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


def get_graph_time_values(interval):
    # helper values for building graph
    today = dt.date.today()
    x_r = None
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
    return x_r, x_name, hover

@callback(
    Output("total_contributor_growth", "figure"),
    [
        Input("contributions", "data"),
        Input("contributor-growth-time-interval", "value")
    ]
)
def total_contributor_growth(data, bin_size):
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
    df_contrib["day"] = pd.DatetimeIndex(df_contrib['created_at']).day

    # get all of the unique entries by contributor ID
    df_contrib = df_contrib.drop_duplicates(subset=["cntrb_id"])

    if(bin_size == -1):
        fig = contributor_growth_line_bar(df_contrib)
    else:
        fig = contributor_growth_bar_graph(df_contrib, bin_size)
    
    # return the simple line graph
    return fig

def contributor_growth_bar_graph(df_contrib, bin_size):

    """
        Group-by determined by the radio button options.
        Aggregation is the number of rows per time bin.
        Days, Months, Years are all options.
    """
    if(bin_size == "D1"):
        group = df_contrib.groupby(
            pd.Grouper(key='created_at', axis=0, 
                      freq='1D')).size()
    elif(bin_size == "M1"):
        group = df_contrib.groupby(
            pd.Grouper(key='created_at', axis=0, 
                      freq='1M')).size()
    else:
        group = df_contrib.groupby(
            pd.Grouper(key='created_at', axis=0, 
                      freq='1Y')).size()

    # reset index from group-by aggregation step
    group = group.reset_index()
    # rename the columns for clarity
    group = group.rename(columns={'created_at': 'date', 0:'count'})

    # correction for year binning - 
    # rounded up to next year so this is a simple patch
    if(bin_size == "M12"):
        group["date"] = group["date"].dt.year

    # create the graph
    fig = px.bar(group, x="date", y='count')

    # make the bars thicker for further-spaced values
    # so that we can see the per-day increases clearly.
    fig.update_traces(marker_color='blue',
                  marker_line_color='blue',
                  selector=dict(type="bar"))

    # add the date-range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                        label="1m",
                        step="month",
                        stepmode="backward"),
                    dict(count=6,
                        label="6m",
                        step="month",
                        stepmode="backward"),
                    dict(count=1,
                        label="YTD",
                        step="year",
                        stepmode="todate"),
                    dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    # label the figure correctly.
    fig.update_layout(
        xaxis_title = "Time",
        yaxis_title = "Number of Contributors"
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
        x='created_at', 
        y='index',
    )

    """
        Ref. for this awesome button thing:
        https://plotly.com/python/range-slider/
    """
    # add the date-range selector
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                        label="1m",
                        step="month",
                        stepmode="backward"),
                    dict(count=6,
                        label="6m",
                        step="month",
                        stepmode="backward"),
                    dict(count=1,
                        label="YTD",
                        step="year",
                        stepmode="todate"),
                    dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    # label the figure correctly
    fig.update_layout(
        xaxis_title = "Time",
        yaxis_title = "Number of Contributors"
    )
    return fig
