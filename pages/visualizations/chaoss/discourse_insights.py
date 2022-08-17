from re import template
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import callback, html, dcc
#from jupyter_dash import JupyterDash
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from sqlalchemy import text,create_engine
import psycopg2
import plotly.express as px
from utils.graph_utils import get_graph_time_values
import logging

#creating postgres connection and connecting to the database
POSTGRESS_ADDRESS = 'augur.chaoss.io'
POSTGRES_PORT = '5432'
POSTGRES_USERNAME = 'mlgsoc'
POSTGRES_PASSWORD = 'gsocks3000!'
POSTGRES_DBNAME = 'augur-0.21.1'

postgres_str = ('postgresql://{username}:{password}@{address}:{port}/{dbname}'.
                format(username = POSTGRES_USERNAME, password = POSTGRES_PASSWORD, address = POSTGRESS_ADDRESS,
                      port = POSTGRES_PORT, dbname = POSTGRES_DBNAME))

conn = create_engine(postgres_str)

discourse_sql_query = '''
                    SELECT
	                  prmr.repo_id repo_id,
	                  prmr.msg_id,
	                  di.discourse_act,
                        msg.msg_timestamp,
	                  max(di.data_collection_date) max_date
	                  FROM
	            augur_data.pull_request_message_ref prmr,
	            augur_data.discourse_insights di,
	            augur_data.message msg 
                  WHERE
	            prmr.msg_id = di.msg_id 
	            AND msg.msg_id = prmr.msg_id 
	            AND prmr.repo_id = 25457
                  group by 1,2,3,4
	            UNION
                  SELECT
	            imr.repo_id repo_id,
	            imr.msg_id,
	            di.discourse_act,
                  msg.msg_timestamp,
	            max(di.data_collection_date) max_date
	            FROM
	            augur_data.issue_message_ref imr,
	            augur_data.discourse_insights di,
	            augur_data.message msg, 
	            augur_data.issues i
                  WHERE
	            imr.msg_id = di.msg_id 
	            AND msg.msg_id = imr.msg_id 
	            AND imr.issue_id = i.issue_id
	            AND imr.repo_id = 25457
	            AND i.pull_request IS NULL 
                  group by 1,2,3,4
                  order by 4 desc, 2
                  '''


gc_discourse_insights = dbc.Card(
      [dbc.CardBody(
            [
                  html.H4("Pull Request and Issue Counts Over Time", className = "card-title", style={"text-align" : "center"}),
                  dbc.Popover(
                        [dbc.PopoverHeader("Graph Info:"),
                         dbc.PopoverBody("This graph gives the count of pull requests and issues per discourse act over time."),
                        ],
                        id = "chaoss-popover-4",
                        target = "chaoss-popover-target-4",
                        placement = "top",
                        is_open = False,
                  ),
                  dcc.Loading(
                        children = [dcc.Graph(id = "issue-counts-per-discount")],
                        color = "#119DFF",
                        type = "dot",
                        fullscreen = False,
                  ),
                  dbc.Form(
                        [
                              dbc.Row(
                                    [
                                          dbc.Label(
                                                "Date Interval",
                                                html_for = "issue-time-interval",
                                                width = "auto",
                                                style = {"font-weight" : "bold"},
                                          ),
                                          dbc.Col(
                                                dbc.RadioItems(
                                                      id = "issue-time-interval",
                                                      options = [
                                                            {"label" : "Day", "value" : 86400000},
                                                            {"label" : "Week", "value" : 60480000},
                                                            {"label" : "Month", "value" : "M1"},
                                                            {"label" : "Year", "value" : "M12"},
                                                      ],
                                                      value = "M1",
                                                      inline = True,
                                                ),
                                                className = "iss-4",
                                          ),
                                          dbc.Col(
                                                dbc.Button(
                                                      "About Graph", id = "chaoss-popover-target-4", color = "secondary", size = "small"
                                                ),
                                                width = "auto",
                                                style = {"padding-top" : ".5em"},
                                          ),
                                    ],
                                    align = "center",
                              )
                        ]
                  )
            ]
      ),
      ],
      color = "light",
)

#Callback to provide a graph description on clicking About Graph Button
@callback(
      Output("chaoss-popover-4", "is_open"),
      [Input("chaoss-popover-target-4", "n_clicks")],
      [State("chaoss-popover-4", "is_open")],
)
def toggle_popover_4(n, is_open):
      if n:
            return not is_open
      return is_open

@callback(
      Output("issue-counts-per-discount", "figure"),
      Input("issue-time-interval", "value"),
)

def update_graph(interval):
     logging.debug("PULL_REQUESTS_AND_ISSUES_OVER_TIME_VIZ - START") 
     #if interval == 86400000:
     #      df = pd.read_sql(discourse_sql_query.format('day', 25457), con = conn) 
     #elif interval == 60480000:
     #      df = pd.read_sql(discourse_sql_query.format('week', 25457), con = conn) 
     #elif interval == 'M1':
     #      df = pd.read_sql(discourse_sql_query.format('month', 25457), con = conn) 
     #else:
     #      df = pd.read_sql(discourse_sql_query.format('year', 25457), con = conn) 
     #df['max_date'] = pd.to_datetime(df['max_date'], utc = True, format = "%Y-%m-%d")
     #df['max_date'] = df['max_date'].astype(int)

     df = pd.read_sql(discourse_sql_query.format(25457), con = conn)
     logging.debug(df)
     df = df.reset_index()
     x_r, x_name, hover, period = get_graph_time_values(interval)

     #negative_reaction_data = df[df['discourse_act'] == 'negativereaction'].reset_index().rename(columns = {'discourse_counts' : 'NegativeReaction'})
     #answer_data = df[df['discourse_act'] == 'answer'].reset_index().rename(columns = {'discourse_counts' : 'Answer'})
     #elaboration_data = df[df['discourse_act'] == 'elaboration'].reset_index().rename(columns = {'discourse_counts' : 'Elaboration'})
     #agreement_data = df[df['discourse_act'] == 'agreement'].reset_index().rename(columns = {'discourse_counts' : 'Agreement'})
     #question_data = df[df['discourse_act'] == 'question'].reset_index().rename(columns = {'discourse_counts' : 'Question'})
     #humor_data = df[df['discourse_act'] == 'humor'].reset_index().rename(columns = {'discourse_counts' : 'Humor'})
     #disagreement_data = df[df['discourse_act'] == 'disagreement'].reset_index().rename(columns = {'discourse_counts' : 'Disagreement'})
     #announcement_data = df[df['discourse_act'] == 'announcement'].reset_index().rename(columns = {'discourse_counts' : 'Announcement'})
     #appreciation_data = df[df['discourse_act'] == 'appreciation'].reset_index().rename(columns = {'discourse_counts' : 'Appreciation'})

     #grouping the data based on data_collection_date, discourse acts
     negative_reaction_data = (df[df['discourse_act'] == 'negativereaction'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'NegativeReaction'}))
     answer_data = (df[df['discourse_act'] == 'answer'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Answer'}))
     elaboration_data = (df[df['discourse_act'] == 'elaboration'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Elaboration'}))
     agreement_data = (df[df['discourse_act'] == 'agreement'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Agreement'}))
     question_data = (df[df['discourse_act'] == 'question'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Question'}))
     humor_data = (df[df['discourse_act'] == 'humor'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Humor'}))
     disagreement_data = (df[df['discourse_act'] == 'Disagreement'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Disagreement'}))
     announcement_data = (df[df['discourse_act'] == 'announcement'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Announcement'}))
     appreciation_data = (df[df['discourse_act'] == 'appreciation'].groupby(by = df.max_date.dt.to_period(period))['msg_id'].nunique().reset_index().rename(columns = {'msg_id' : 'Appreciation'}))

     #df = pd.merge(negative_reaction_data, answer_data, elaboration_data, agreement_data, question_data, humor_data, disagreement_data, announcement_data, appreciation_data, on = ['discourse_act', 'data_collection_date'], how = "outer")
     #merging the data for building a histogram for each day,week,month and year
     df = pd.merge(negative_reaction_data, answer_data, on = 'max_date', how = 'outer')
     df = pd.merge(df, elaboration_data, on = 'max_date', how = 'outer')
     df = pd.merge(df, agreement_data, on = 'max_date', how = 'outer')
     df = pd.merge(df, question_data, on = 'max_date', how = 'outer')
     df = pd.merge(df, humor_data, on = 'max_date', how = 'outer')
     df = pd.merge(df, disagreement_data, on = 'max_date', how = 'outer')
     df = pd.merge(df, announcement_data, on = 'max_date', how = 'outer')
     df = pd.merge(df, appreciation_data, on = 'max_date', how = 'outer')
     df['max_date'] = df['max_date'].dt.to_timestamp()

     
     #graph generation
     if df is not None:
           fig = px.histogram(df, x = "max_date", y = [df['NegativeReaction'], df['Answer'], df['Elaboration'], df['Agreement'], df['Question'], df['Humor'], df['Disagreement'], df['Announcement'], df['Appreciation']], range_x = x_r, labels = {"x" : x_name, "y": "Pull Requests and Issues"}, template = "minty",)
           fig.update_traces(xbins_size = interval, hovertemplate = hover + "<br> Pull Requests and Issues: %{y}<br><extra></extra>",)
           fig.update_xaxes(showgrid = True, ticklabelmode = "period", dtick = interval, rangeslider_yaxis_rangemode = "match",)
           fig.update_layout(xaxis_title = x_name, legend_title_text = "Discourse Acts", yaxis_title = "Number of Pull Requests and Issues", margin_b = 40,)
           logging.debug("PULL_REQUESTS_AND_ISSUES_OVER_TIME_VIZ - END") 
           return fig
     else:
           return None      