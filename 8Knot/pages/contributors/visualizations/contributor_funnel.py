from dash import html, dcc, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import logging
import time
import app
import cache_manager.cache_facade as cf
from pages.utils.job_utils import nodata_graph
from queries.contributors_query import contributors_funnel_query as cfq  # you'll need this
from pages.utils.graph_utils import color_seq

PAGE = "contributors"
VIZ_ID = "contributor-funnel"

gc_contributor_funnel = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contributor Funnel",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            "Shows contributor engagement stages and drop-off rates for a selected repository or group."
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Row(
                    dbc.Button(
                        "About Graph",
                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                        color="secondary",
                        size="small",
                    ),
                    style={"paddingTop": ".5em"},
                ),
            ]
        ),
    ],
)


@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_funnel_popover(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    [
        Input("repo-choices", "data"),
        Input("bot-switch", "value"),
    ],
    background=True,
)
def create_contributor_funnel_figure(repolist, bot_switch):
    while not_cached := cf.get_uncached(func_name=cfq.__name__, repolist=repolist):
        logging.warning(f"{VIZ_ID}- WAITING ON DATA TO BECOME AVAILABLE")
        time.sleep(0.5)

    df = cf.retrieve_from_cache(tablename=cfq.__name__, repolist=repolist)

    if df.empty:
        logging.warning("CONTRIBUTOR_FUNNEL - NO DATA")
        return nodata_graph

    if bot_switch:
        df = df[~df["cntrb_id"].isin(app.bots_list)]
    logging.warning(f"CONTRIBUTOR_FUNNEL - Data shape after bot filter: {df.shape}")

    # create simple funnel count
    funnel_stages = {
        "Engaged Contributors": df["username"].nunique(),
        "Issue Creators": df[df["created_issue"] == 1]["username"].nunique(),
        "PR Openers": df[df["opened_pr"] == 1]["username"].nunique(),
        "PR Commenters": df[df["pr_commented"] == 1]["username"].nunique(),
    }

    funnel_df = pd.DataFrame({
        "Stage": list(funnel_stages.keys()),
        "Contributors": list(funnel_stages.values())
    })

    fig = px.funnel(funnel_df, x="Contributors", y="Stage", color="Stage", color_discrete_sequence=color_seq)

    fig.update_layout(
        margin_b=40,
        font=dict(size=14),
        xaxis_title="Number of Contributors",
        yaxis_title="Stage",
    )

    return fig
