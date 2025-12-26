import dash_bootstrap_components as dbc
from dash import callback
from dash.dependencies import Input, Output
import pandas as pd
import logging
import plotly.express as px
from pages.utils.graph_utils import baby_blue
from pages.utils.job_utils import nodata_graph
from pages.utils.query_status import load_query_data
from queries.contributors_query import contributors_query as ctq
import app
import pages.utils.preprocessing_utils as preproc_utils
from components.visualization import VisualizationAIO

PAGE = "contributors"
VIZ_ID = "contrib-drive-repeat"

gc_contrib_drive_repeat = VisualizationAIO(
    PAGE,
    VIZ_ID,
    graph_info="""
    Visualizes the per-quarter consistency of contributors.\n
    A contributor is counted in an 'Action' category if they have made at least 'Contributions Required'\n
    contributions within the quarter. For example, if 'Contributions Required' is 2, then a contributor will\n
    be counted once in 'Open PR' and in 'PR Comment' if they made 2 or more PR's AND commented 2 or more times on PRs.\n
    Please read definition of 'Contributor Consistency' on Info page.
    """,
    controls=[
        dbc.Label(
            "Contributions Required:",
            html_for=f"contributions-required-{PAGE}-{VIZ_ID}",
            width={"size": "auto"},
        ),
        dbc.Col(
            dbc.Input(
                id=f"contributions-required-{PAGE}-{VIZ_ID}",
                type="number",
                min=1,
                max=15,
                step=1,
                value=4,
                size="sm",
                style={"width": "80px"},
                className="dark-input",
            ),
            className="me-2",
            width=2,
        ),
        dbc.Label(
            "Graph View:",
            html_for=f"graph-view-{PAGE}-{VIZ_ID}",
            width={"size": "auto"},
        ),
        dbc.Col(
            dbc.RadioItems(
                id=f"graph-view-{PAGE}-{VIZ_ID}",
                options=[
                    {
                        "label": "Repeat",
                        "value": "repeat",
                    },
                    {
                        "label": "Drive-Thru",
                        "value": "drive",
                    },
                ],
                value="drive",
                inline=True,
                className="custom-radio-buttons",
            ),
        ),
    ],
    class_name="dark-card",
    id="drive-throughs",
)


# callback for dynamically changing the graph title
@callback(
    Output(f"graph-title-{PAGE}-{VIZ_ID}", "children"),
    Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
)
def graph_title(view):
    title = ""
    if view == "drive":
        title = "Drive-Thru Contributions Per Quarter"
    else:
        title = "Repeat Contributions Per Quarter"
    return title


# call back for drive by vs commits over time graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input(f"contributions-required-{PAGE}-{VIZ_ID}", "value"),
        Input(f"graph-view-{PAGE}-{VIZ_ID}", "value"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def repeat_drive_by_graph(repolist, contribs, view, bot_switch):
    # Wait for and load query data (includes timeout, error handling, and validation)
    df = load_query_data(ctq, repolist, VIZ_ID)
    if df is None:
        return nodata_graph

    df = preproc_utils.contributors_df_action_naming(df)

    # remove bot data
    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]

    # function for all data pre processing
    df_cont_subset = process_data(df, view, contribs)

    # test if there is data
    if df_cont_subset.empty:
        logging.warning("CONTRIB DRIVE REPEAT - NO DRIVE OR REPEAT DATA")
        return nodata_graph

    fig = create_figure(df_cont_subset)

    return fig


def process_data(df, view, contribs):
    # convert to datetime objects with consistent column name
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    # df.rename(columns={"created_at": "created"}, inplace=True)

    # graph on contribution subset
    contributors = df["cntrb_id"][df["rank"] == contribs].to_list()
    df_cont_subset = pd.DataFrame(df)

    # filtering data by view
    if view == "drive":
        df_cont_subset = df_cont_subset.loc[~df_cont_subset["cntrb_id"].isin(contributors)]
    else:
        df_cont_subset = df_cont_subset.loc[df_cont_subset["cntrb_id"].isin(contributors)]

    # reset index to be ready for plotly
    df_cont_subset = df_cont_subset.reset_index()

    return df_cont_subset


def create_figure(df_cont_subset):
    # create plotly express histogram
    fig = px.histogram(
        df_cont_subset,
        x="created_at",
        color="Action",
        color_discrete_sequence=baby_blue,
    )

    # creates bins with 3 month size and customizes the hover value for the bars
    fig.update_traces(
        xbins_size="M3",
        hovertemplate="Date: %{x}" + "<br>Amount: %{y}",
    )

    # update xaxes to align for the 3 month bin size
    fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M3")

    # layout styling
    fig.update_layout(
        xaxis_title="Quarter",
        yaxis_title="Contributions",
        margin_b=40,
        font=dict(size=14),
    )
    return fig
