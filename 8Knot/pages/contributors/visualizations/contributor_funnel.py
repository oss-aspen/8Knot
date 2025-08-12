from dash import html, dcc, callback
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import logging
import time
import app

from cache_manager import cache_facade as cf
from pages.utils.job_utils import nodata_graph
from queries.contributors_query import contributors_funnel_query as cfq
from pages.utils.graph_utils import color_seq

PAGE = "contributors"
VIZ_ID = "contributor-funnel"

gc_contributor_funnel = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3("Contributor Funnel", className="card-title", style={"textAlign": "center"}),
                dbc.Popover(
                    [dbc.PopoverHeader("Graph Info:"), dbc.PopoverBody("Shows contributor engagement stages and drop-off rates for a selected repository or group.")],
                    id=f"popover-{PAGE}-{VIZ_ID}", target=f"popover-target-{PAGE}-{VIZ_ID}", placement="top", is_open=False,
                ),
                dcc.Store(id=f"{PAGE}-{VIZ_ID}-cache-signal"),
                dcc.Loading(dcc.Graph(id=f"{PAGE}-{VIZ_ID}", figure=nodata_graph)),
                dbc.Row(dbc.Button("About Graph", id=f"popover-target-{PAGE}-{VIZ_ID}", color="secondary", size="small"), style={"paddingTop": ".5em"}),
            ]
        ),
    ],
)

@callback(
    Output(f"{PAGE}-{VIZ_ID}-cache-signal", "data"),
    Input("repo-choices", "data"),
    background=True,
)
def update_contributor_funnel_cache(repolist):
    """
    This background callback checks the cache. If data is missing, it runs the
    query itself, stores the result, and then sends the completion signal.
    """
    if not repolist:
        logging.warning(f"{VIZ_ID} - CACHE_MANAGER: No repos selected. Preventing update.")
        raise PreventUpdate

    not_cached = cf.get_uncached(func_name=cfq.__name__, repolist=repolist)

    if not not_cached:
        logging.info(f"{VIZ_ID} - CACHE_MANAGER: Data already cached. Triggering graph update.")
        return {"status": "complete", "timestamp": time.time()}

    logging.warning(f"{VIZ_ID} - CACHE_MANAGER: Fetching data for {len(not_cached)} uncached repos.")

    df_new = cfq(not_cached)
    if df_new is not None and not df_new.empty:
        cf.store_in_cache(tablename=cfq.__name__, df=df_new)
        logging.warning(f"{VIZ_ID} - CACHE_MANAGER: Successfully cached new data.")
    else:
        logging.warning(f"{VIZ_ID} - CACHE_MANAGER: Query ran but returned no new data.")

    return {"status": "complete", "timestamp": time.time()}


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Input(f"{PAGE}-{VIZ_ID}-cache-signal", "data"),
    Input("bot-switch", "value"),
    State("repo-choices", "data"),
)
def create_contributor_funnel_figure(cache_signal, bot_switch, repolist):
    """
    This callback will run whenever the cache_signal is updated.
    """
    if not cache_signal or not repolist or cache_signal.get("status") != "complete":
        return nodata_graph

    logging.warning(f"{VIZ_ID} - FIGURE: Signal received. Generating graph.")
    df = cf.retrieve_from_cache(tablename=cfq.__name__, repolist=repolist)

    if df.empty:
        return nodata_graph

    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]
    if df.empty:
        return nodata_graph

    funnel_stages = {
        "Engaged Contributors": df["username"].nunique(),
        "Issue Creators": df[df["created_issue"] == 1]["username"].nunique(),
        "PR Openers": df[df["opened_pr"] == 1]["username"].nunique(),
        "PR Commenters": df[df["pr_commented"] == 1]["username"].nunique(),
    }
    funnel_df = pd.DataFrame({"Stage": list(funnel_stages.keys()), "Contributors": list(funnel_stages.values())})

    fig = px.funnel(funnel_df, x="Contributors", y="Stage", color="Stage", color_discrete_sequence=color_seq)
    fig.update_layout(
        margin_b=40, font=dict(size=14),
        xaxis_title="Number of Contributors", yaxis_title="Stage",
        showlegend=False
    )
    return fig

@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks"),
    State(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
)
def toggle_funnel_popover(n, is_open):
    if n:
        return not is_open
    return is_open