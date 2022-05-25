from turtle import title
from dash import html, callback_context, callback, dcc
import plotly.express as px
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
from app import app
import pandas as pd
import datetime as dt
import numpy as np
import warnings
warnings.filterwarnings("ignore")


layout = dbc.Container([
    
    dbc.Row([
        dbc.Col([
            html.H1(children="Chaoss WIP Page - live update")
            ]
        )
        ]
    ),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='cont-drive-repeat'),

            dbc.Form(
                dbc.Row(
                    [
                    dbc.Label('Contributions Required:', html_for='num_contributions', width={"offset": 1, "size":"auto"},
                                style={'font-weight': 'bold'}),
                    dbc.Col([
                        dbc.Input( id='num_contributions', type = 'number', min = 1, max= 15,step =1, value = 4)],
                        className="me-3", width= 2),

                    dbc.Label('Graph View:', html_for='drive-repeat', width="auto",style={'font-weight': 'bold'}),
                    dbc.Col([
                        dbc.RadioItems(
                            id='drive-repeat',
                            options=[
                                {'label': 'Repeat', 'value': 'repeat'},
                                {'label': 'Drive-By', 'value': 'drive'},
                                ],
                            value='drive',)
                        ],className="me-3",
                        ),
                    ],className="g-2",align="center",justify="start"
                )
            ),
            ],
        ),
        dbc.Col([
            dcc.Graph(id='first-time-contributors'),
            ],
        ),
        ]
    ),

    dbc.Row([
        dbc.Col([

            dcc.Graph(id='contributors-over-time'),

            dbc.Form(
                dbc.Row(
                    [
                    dbc.Label('Contributions Required:', html_for='num_contribs_req', width={"offset": 1, "size":"auto"},
                                style={'font-weight': 'bold'}),
                    dbc.Col([
                        dbc.Input( id='num_contribs_req', type = 'number', min = 1, max= 15,step =1, value = 4)],
                        className="me-3", width= 2),

                    dbc.Label('Date Interval:', html_for='contrib-time-interval', width="auto",style={'font-weight': 'bold'}),
                    dbc.Col([
                        dbc.RadioItems(
                            id='contrib-time-interval',
                            options=[
                                {'label': 'Day', 'value': 86400000}, #days in milliseconds for ploty use  
                                {'label': 'Week', 'value': 604800000}, #weeks in milliseconds for ploty use
                                {'label': 'Month', 'value': 'M1'},
                                {'label': 'Year', 'value': 'M12'}
                                ],
                            value='M1',)
                        ],className="me-3",
                        ),
                    ],className="g-2",align="center",justify="start"
                )
            ),
            ],
        ),
        ]
    )

], fluid= True)

#call back for drive by vs commits over time graph   
@callback(
    Output('cont-drive-repeat', 'figure'),
    [Input('contributions', 'data'),
    Input('num_contributions','value'),
    Input('drive-repeat','value')
    ]
)
def create_graph(data,contribs,view):
    #graph on contribution subset
    df_cont = pd.DataFrame(data)
    contributors = df_cont['cntrb_id'][df_cont['rank']== contribs].to_list()
    df_cont_subset = pd.DataFrame(data)


    #Inputs for Title of graph
    title= ''
    if view == 'drive':
        df_cont_subset = df_cont_subset.loc[~df_cont_subset['cntrb_id'].isin(contributors)]
        title = "Drive By Contributions Per Quarter"
    else: 
        df_cont_subset = df_cont_subset.loc[df_cont_subset['cntrb_id'].isin(contributors)]
        title = "Repeat Contributions Per Quarter"

    # reset index to be ready for plotly
    df_cont_subset = df_cont_subset.reset_index()

    
    #graph geration
    if(df_cont_subset is not None):
        fig = px.histogram(df_cont_subset, x="created_at", color="Action")
        fig.update_traces(xbins_size='M3', hovertemplate= "Date: %{x}" +
                                                            "<br>Amount: %{y}<br><extra></extra>")
        fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick='M3')
        fig.update_layout(
            title={'text':title,
                      'font':{'size':28},'x':0.5,'xanchor':'center'},
        xaxis_title="Quarter",
        yaxis_title="Contributions")
        return fig
    else:
        return None


@callback(Output("first-time-contributors", "figure"), Input("contributions", "data"))
def create_graph(data):
    df_cont = pd.DataFrame(data)

    # selection for 1st contribution only
    df_cont = df_cont[df_cont["rank"] == 1]

    # reset index to be ready for plotly
    df_cont = df_cont.reset_index()

    # Graph generation
    if df_cont is not None:
        fig = px.histogram(df_cont, x="created_at", color="Action")
        fig.update_traces(
            xbins_size="M3",
            hovertemplate="Date: %{x}" + "<br>Amount: %{y}<br><extra></extra>",
        )
        fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M3")
        fig.update_layout(
            title={'text':"First Time Contributions Per Quarter",
                      'font':{'size':28},'x':0.5,'xanchor':'center'},
        xaxis_title="Quarter",
        yaxis_title="Contributions")
        return fig
    else:
        return None  

@callback(
    Output('contributors-over-time', 'figure'),
    [Input('contributions', 'data'),
    Input('num_contribs_req','value'),
    Input('contrib-time-interval','value')]
)
def create_graph(data,contribs,interval):
    df_cont = pd.DataFrame(data)
    df_cont['created_at'] = pd.to_datetime(df_cont['created_at'], utc=True, format= '%Y-%m-%d')

    #create column for identifying Drive by and Repeat Contributors 
    contributors = df_cont['cntrb_id'][df_cont['rank']== contribs].to_list()
    df_cont["type"] = np.where(df_cont['cntrb_id'].isin(contributors), "Repeat", "Drive-By")

    # reset index to be ready for plotly
    df_cont = df_cont.reset_index()

    #time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)


    #graphs generated for aggregation by time interval
    drive_temp = df_cont[df_cont['type']=="Drive-By"].groupby(by = df_cont.created_at.dt.to_period(period))["cntrb_id"].nunique().reset_index().rename(columns={"cntrb_id": "Drive-By"})
    repeat_temp= df_cont[df_cont['type']=="Repeat"].groupby(by = df_cont.created_at.dt.to_period(period))["cntrb_id"].nunique().reset_index().rename(columns={"cntrb_id": "Repeat"})
    df_final = pd.merge(repeat_temp, drive_temp, on='created_at', how='outer')
    df_final['created_at']= df_final['created_at'].dt.to_timestamp()

    #graph geration
    if(df_final is not None):
        fig = px.histogram(df_final, x="created_at",y= [df_final["Repeat"],df_final["Drive-By"]], range_x=x_r,labels={'x':x_name, 'y':'Contributors'})
        fig.update_traces(xbins_size=interval , hovertemplate =hover + "<br>Contributors: %{y}<br><extra></extra>" )
        fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick=interval,rangeslider_yaxis_rangemode="match" )
        fig.update_layout(
            title={'text':"Contributor Types over Time",
                      'font':{'size':28},'x':0.5,'xanchor':'center'},
        xaxis_title=x_name,
        legend_title_text='Type',
        yaxis_title="Number of Contributors")
        return fig
    else:
        return None  


def get_graph_time_values(interval):
    #helper values for building graph 
    today = dt.date.today()
    x_r = None
    x_name = "Year"
    hover = "Year: %{x|%Y}"
    period = 'Y'

    
    #graph input values based on date interval selection
    if interval == 86400000: #if statement for days
        x_r = [str(today-dt.timedelta(weeks=4)),str(today)]
        x_name = "Day"
        hover = "Day: %{x|%b %d, %Y}"
        period = "D"
    elif interval == 604800000: #if statmement for weeks 
        x_r = [str(today-dt.timedelta(weeks=30)),str(today)]
        x_name = "Week"
        hover = "Week: %{x|%b %d, %Y}"
        period = "W"
    elif interval =='M1': #if statement for months
        x_r = [str(today-dt.timedelta(weeks=104)),str(today)]
        x_name = "Month"
        hover = "Month: %{x|%b %Y}"
        period = "M"
    return x_r, x_name, hover, period

