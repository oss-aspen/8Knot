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







# # contributor_funnel.py (FINAL, WORKING VERSION)
# import logging
# import time
# from datetime import datetime, timedelta
# import dash_bootstrap_components as dbc
# import pandas as pd
# import plotly.express as px
# from dash import dcc, html, callback
# from dash.dependencies import Input, Output, State
# from dash.exceptions import PreventUpdate
# import app
# from cache_manager import cache_facade as cf
# from pages.utils.job_utils import nodata_graph
# from queries.contributors_query import contributors_funnel_query as cfq

# PAGE = "contributors"
# VIZ_ID = "contributor-funnel"

# gc_contributor_funnel = dbc.Card(
#     [
#         dbc.CardBody(
#             [
#                 html.H3("Contributor Journey", className="card-title", style={"textAlign": "center"}),
#                 dbc.Row([
#                     dbc.Col(html.Label("Define Inactivity (days with no contributions):"), width="auto"),
#                     dbc.Col(dcc.Input(id=f"{PAGE}-{VIZ_ID}-inactivity-days", type="number", value=90, min=30, step=30), width=2),
#                 ], justify="center", align="center", className="mb-3"),
#                 dbc.Row([
#                     dbc.Col(dcc.Loading(dcc.Graph(id=f"{PAGE}-{VIZ_ID}-progression"))),
#                     dbc.Col(dcc.Loading(dcc.Graph(id=f"{PAGE}-{VIZ_ID}-inactivity"))),
#                 ]),
#                 dbc.Popover(
#                     [dbc.PopoverHeader("Graph Info:"), dbc.PopoverBody("Left: Shows contributor progression. Right: Shows how many contributors at each stage are inactive.")],
#                     id=f"popover-{PAGE}-{VIZ_ID}", target=f"popover-target-{PAGE}-{VIZ_ID}", placement="top", is_open=False,
#                 ),
#                 dbc.Row(dbc.Button("About Graph", id=f"popover-target-{PAGE}-{VIZ_ID}", color="secondary", size="small"), style={"paddingTop": ".5em"}),
#             ]
#         ),
#     ],
# )

# @callback(
#     Output(f"{PAGE}-{VIZ_ID}-progression", "figure"),
#     Output(f"{PAGE}-{VIZ_ID}-inactivity", "figure"),
#     Input("repo-choices", "data"),
#     Input("bot-switch", "value"),
#     Input(f"{PAGE}-{VIZ_ID}-inactivity-days", "value"),
#     background=True,
# )
# def create_contributor_journey_figures(repolist, bot_switch, inactivity_days):
#     if not repolist or not inactivity_days:
#         raise PreventUpdate

#     while not_cached := cf.get_uncached(func_name=cfq.__name__, repolist=repolist):
#         time.sleep(1)

#     df = cf.retrieve_from_cache(func_name=cfq.__name__, repolist=repolist)
#     if df.empty:
#         return nodata_graph, nodata_graph

#     if bot_switch and "cntrb_id" in df.columns:
#         df = df[~df["cntrb_id"].isin(app.bots_list)]
#     if df.empty:
#         return nodata_graph, nodata_graph
        
#     d0_mask = pd.Series([False] * len(df))
#     if 'first_engagement_date' in df.columns:
#         df['first_engagement_date'] = pd.to_datetime(df['first_engagement_date'], errors='coerce').fillna(pd.NaT)
#         d0_mask = df['first_engagement_date'].notna()

#     d1_mask = pd.Series([False] * len(df))
#     if 'first_contribution_date' in df.columns:
#         df['first_contribution_date'] = pd.to_datetime(df['first_contribution_date'], errors='coerce').fillna(pd.NaT)
#         d1_mask = df['first_contribution_date'].notna()

#     d2_mask = pd.Series([False] * len(df))
#     if 'pr_merged_count' in df.columns:
#         df['pr_merged_count'] = df['pr_merged_count'].fillna(0)
#         d2_mask = df['pr_merged_count'] > 0

#     is_inactive_mask = pd.Series([False] * len(df))
#     if 'last_activity_date' in df.columns:
#         df['last_activity_date'] = pd.to_datetime(df['last_activity_date'], errors='coerce').fillna(pd.NaT)
#         if not df['last_activity_date'].isnull().all():
#             tz = df['last_activity_date'].dt.tz
#             if tz: inactivity_threshold_date = datetime.now(tz) - timedelta(days=inactivity_days)
#             else:
#                 inactivity_threshold_date = datetime.now() - timedelta(days=inactivity_days)
#                 if pd.api.types.is_datetime64_ns_dtype(df['last_activity_date']):
#                     df['last_activity_date'] = df['last_activity_date'].dt.tz_localize(None)
#             is_inactive_mask = df['last_activity_date'] < inactivity_threshold_date

#     d0_total = df.loc[d0_mask, 'username'].nunique() if 'username' in df.columns else 0
#     d1_total = df.loc[d1_mask, 'username'].nunique() if 'username' in df.columns else 0
#     d2_total = df.loc[d2_mask, 'username'].nunique() if 'username' in df.columns else 0
    
#     progression_df = pd.DataFrame([
#         {'Stage': 'D0: Initial Engagement', 'Contributors': d0_total}, {'Stage': 'D1: First Contribution', 'Contributors': d1_total}, {'Stage': 'D2: Sustained Contribution', 'Contributors': d2_total},
#     ])
    
#     inactive_at_d0 = df.loc[d0_mask & is_inactive_mask, 'username'].nunique() if 'username' in df.columns else 0
#     inactive_at_d1 = df.loc[d1_mask & is_inactive_mask, 'username'].nunique() if 'username' in df.columns else 0
#     inactive_at_d2 = df.loc[d2_mask & is_inactive_mask, 'username'].nunique() if 'username' in df.columns else 0

#     inactivity_df = pd.DataFrame([
#         {'Stage': 'D0 Contributors', 'Inactive Count': inactive_at_d0, 'Total': d0_total}, {'Stage': 'D1 Contributors', 'Inactive Count': inactive_at_d1, 'Total': d1_total}, {'Stage': 'D2 Contributors', 'Inactive Count': inactive_at_d2, 'Total': d2_total},
#     ])
#     inactivity_df['Active Count'] = inactivity_df['Total'] - inactivity_df['Inactive Count']
    
#     fig_progression = px.funnel(progression_df, x='Contributors', y='Stage', title='Contributor Progression Funnel')
#     fig_progression.update_layout(margin=dict(t=40, b=10, l=10, r=10), showlegend=False)
#     fig_inactivity = px.bar(
#         inactivity_df, y='Stage', x=['Active Count', 'Inactive Count'], orientation='h', title=f'Contributor Status (Inactive > {inactivity_days} Days)',
#         labels={'value': 'Number of Contributors'}, color_discrete_map={'Active Count': '#1f77b4', 'Inactive Count': '#ff6347'}
#     )
#     fig_inactivity.update_layout(margin=dict(t=40, b=10, l=10, r=10), barmode='stack', yaxis={'categoryorder':'total ascending'})
#     fig_inactivity.update_yaxes(title_text="") 
    
#     return fig_progression, fig_inactivity

# @callback(
#     Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
#     Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks"),
#     State(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
# )
# def toggle_funnel_popover(n, is_open):
#     if n: return not is_open
#     return is_open 


#contributors_query.py
