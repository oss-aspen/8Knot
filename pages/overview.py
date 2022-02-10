from turtle import title
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

from app import app

# total # contributors - line graph
stocks_df = px.data.stocks()
medals_df = px.data.medals_long()


total_contributors = px.line(stocks_df, x='date', y="GOOG")
total_contributors.update_layout(title="Total # of Contributors over Time", title_x=0.5, title_y=0.9)

total_commits = px.line(stocks_df, x='date', y="MSFT")
total_commits.update_layout(title="Total # of Commits", title_x=0.5, title_y=0.9)

active_users = px.bar(medals_df, x="medal", y="count", color="nation")
active_users.update_layout(title="Active vs. Drifting vs. Gone", title_x=0.5, title_y=0.9)
active_users.update_layout(showlegend=False)

PR_composition = px.bar(medals_df, x="medal", y="count", color="nation")
PR_composition.update_layout(title="Composition of PR's", title_x=0.5, title_y=0.9)
PR_composition.update_layout(showlegend=False)

import plotly.graph_objects as go

years = ['2016','2017','2018']

issues_changes = go.Figure()
issues_changes.add_trace(go.Bar(x=years, y=[500, 600, 700],
                base=[-500,-600,-700],
                marker_color='crimson',
                name='expenses'))
issues_changes.add_trace(go.Bar(x=years, y=[300, 400, 700],
                base=0,
                marker_color='lightslategrey',
                name='revenue'
                ))
issues_changes.update_layout(showlegend=False)
issues_changes.update_layout(title="Issue-count Changes over Time", title_x=0.5, title_y=0.9)


colors = ['lightslategray',] * 5
colors[1] = 'crimson'

new_contributors = go.Figure(data=[go.Bar(
    x=['Feature A', 'Feature B', 'Feature C',
       'Feature D', 'Feature E'],
    y=[20, 14, 23, 25, 22],
    marker_color=colors # marker color can be a single color value or an iterable
)])
new_contributors.update_layout(title='New Contributors per Month', title_x=0.5, title_y=0.9)

layout = html.Div(children=[
    html.H1(children="Overview Page!"),
    html.Div(children=[
        dcc.Graph(figure=total_contributors, style={'display': 'inline-block', 'width': '33%'}),
        dcc.Graph(figure=new_contributors, style={'display': 'inline-block', 'width': '33%'}),
        dcc.Graph(figure=active_users, style={'display': 'inline-block', 'width': '33%'})
    ]),
    html.Div(children=[
        dcc.Graph(figure=total_commits, style={'display': 'inline-block', 'width': '33%'}),
        dcc.Graph(figure=issues_changes, style={'display': 'inline-block', 'width': '33%'}),
        dcc.Graph(figure=PR_composition, style={'display': 'inline-block', 'width': '33%'})
    ])
])

# novel contributors - bar graph

# active vs. drifting vs. gone - stacked bar

# commits over time - line graph

# new commits per time bin - bar graph

# summary of PR's - stacked bar

