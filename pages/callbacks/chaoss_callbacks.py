from dash import callback
import plotly.express as px
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import datetime as dt
import numpy as np
import warnings
import logging

warnings.filterwarnings("ignore")


@callback(
    Output("chaoss-popover-1", "is_open"),
    [Input("chaoss-popover-target-1", "n_clicks")],
    [State("chaoss-popover-1", "is_open")],
)
def toggle_popover_1(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(Output("chaoss-graph-title-1", "children"), Input("drive-repeat", "value"))
def graph_title(view):
    title = ""
    if view == "drive":
        title = "Drive-by Contributions Per Quarter"
    else:
        title = "Repeat Contributions Per Quarter"
    return title


@callback(
    Output("chaoss-popover-2", "is_open"),
    [Input("chaoss-popover-target-2", "n_clicks")],
    [State("chaoss-popover-2", "is_open")],
)
def toggle_popover_2(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("chaoss-popover-3", "is_open"),
    [Input("chaoss-popover-target-3", "n_clicks")],
    [State("chaoss-popover-3", "is_open")],
)
def toggle_popover_3(n, is_open):
    if n:
        return not is_open
    return is_open


# call back for drive by vs commits over time graph
@callback(
    Output("cont-drive-repeat", "figure"),
    [
        Input("contributions", "data"),
        Input("num_contributions", "value"),
        Input("drive-repeat", "value"),
    ],
)
def create_drive_by_graph(data, contribs, view):
    logging.debug("CONTRIB_DRIVE_REPEAT_VIZ - START")

    # graph on contribution subset
    df_cont = pd.DataFrame(data)
    contributors = df_cont["cntrb_id"][df_cont["rank"] == contribs].to_list()
    df_cont_subset = pd.DataFrame(data)

    # filtering data by view
    if view == "drive":
        df_cont_subset = df_cont_subset.loc[~df_cont_subset["cntrb_id"].isin(contributors)]
    else:
        df_cont_subset = df_cont_subset.loc[df_cont_subset["cntrb_id"].isin(contributors)]

    # reset index to be ready for plotly
    df_cont_subset = df_cont_subset.reset_index()

    # graph geration
    if df_cont_subset is not None:
        fig = px.histogram(df_cont_subset, x="created_at", color="Action", template="minty")
        fig.update_traces(
            xbins_size="M3",
            hovertemplate="Date: %{x}" + "<br>Amount: %{y}<br><extra></extra>",
        )
        fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M3")
        fig.update_layout(
            xaxis_title="Quarter",
            yaxis_title="Contributions",
            margin_b=40,
        )
        logging.debug("CONTRIB_DRIVE_REPEAT_VIZ - END")
        return fig
    else:
        return None


@callback(Output("first-time-contributions", "figure"), Input("contributions", "data"))
def create_first_time_contributors_graph(data):
    logging.debug("1ST_CONTRIBUTIONS_VIZ - START")
    df_cont = pd.DataFrame(data)

    # selection for 1st contribution only
    df_cont = df_cont[df_cont["rank"] == 1]

    # reset index to be ready for plotly
    df_cont = df_cont.reset_index()

    # Graph generation
    if df_cont is not None:
        fig = px.histogram(df_cont, x="created_at", color="Action", template="minty")
        fig.update_traces(
            xbins_size="M3",
            hovertemplate="Date: %{x}" + "<br>Amount: %{y}<br><extra></extra>",
        )
        fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M3")
        fig.update_layout(
            xaxis_title="Quarter",
            yaxis_title="Contributions",
            margin_b=40,
        )
        logging.debug("1ST_CONTRIBUTIONS_VIZ - END")
        return fig
    else:
        return None


@callback(
    Output("contributors-over-time", "figure"),
    [
        Input("contributions", "data"),
        Input("num_contribs_req", "value"),
        Input("contrib-time-interval", "value"),
    ],
)
def create_graph(data, contribs, interval):
    logging.debug("CONTRIBUTIONS_OVER_TIME_VIZ - START")

    df_cont = pd.DataFrame(data)
    df_cont["created_at"] = pd.to_datetime(df_cont["created_at"], utc=True, format="%Y-%m-%d")

    # create column for identifying Drive by and Repeat Contributors
    contributors = df_cont["cntrb_id"][df_cont["rank"] == contribs].to_list()
    df_cont["type"] = np.where(df_cont["cntrb_id"].isin(contributors), "Repeat", "Drive-By")

    # reset index to be ready for plotly
    df_cont = df_cont.reset_index()

    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graphs generated for aggregation by time interval
    drive_temp = (
        df_cont[df_cont["type"] == "Drive-By"]
        .groupby(by=df_cont.created_at.dt.to_period(period))["cntrb_id"]
        .nunique()
        .reset_index()
        .rename(columns={"cntrb_id": "Drive-By"})
    )
    repeat_temp = (
        df_cont[df_cont["type"] == "Repeat"]
        .groupby(by=df_cont.created_at.dt.to_period(period))["cntrb_id"]
        .nunique()
        .reset_index()
        .rename(columns={"cntrb_id": "Repeat"})
    )
    df_final = pd.merge(repeat_temp, drive_temp, on="created_at", how="outer")
    df_final["created_at"] = df_final["created_at"].dt.to_timestamp()

    # graph geration
    if df_final is not None:
        fig = px.histogram(
            df_final,
            x="created_at",
            y=[df_final["Repeat"], df_final["Drive-By"]],
            range_x=x_r,
            labels={"x": x_name, "y": "Contributors"},
            template="minty",
        )
        fig.update_traces(
            xbins_size=interval,
            hovertemplate=hover + "<br>Contributors: %{y}<br><extra></extra>",
        )
        fig.update_xaxes(
            showgrid=True,
            ticklabelmode="period",
            dtick=interval,
            rangeslider_yaxis_rangemode="match",
        )
        fig.update_layout(
            xaxis_title=x_name,
            legend_title_text="Type",
            yaxis_title="Number of Contributors",
            margin_b=40,
        )
        logging.debug("CONTRIBUTIONS_OVER_TIME_VIZ - END")
        return fig
    else:
        return None


def get_graph_time_values(interval):
    # helper values for building graph
    today = dt.date.today()
    x_r = None
    x_name = "Year"
    hover = "Year: %{x|%Y}"
    period = "Y"

    # graph input values based on date interval selection
    if interval == 86400000:  # if statement for days
        x_r = [str(today - dt.timedelta(weeks=4)), str(today)]
        x_name = "Day"
        hover = "Day: %{x|%b %d, %Y}"
        period = "D"
    elif interval == 604800000:  # if statmement for weeks
        x_r = [str(today - dt.timedelta(weeks=30)), str(today)]
        x_name = "Week"
        hover = "Week: %{x|%b %d, %Y}"
        period = "W"
    elif interval == "M1":  # if statement for months
        x_r = [str(today - dt.timedelta(weeks=104)), str(today)]
        x_name = "Month"
        hover = "Month: %{x|%b %Y}"
        period = "M"
    return x_r, x_name, hover, period
