from dash import dcc, html
import dash
import dash_bootstrap_components as dbc
import warnings

warnings.filterwarnings("ignore")

dash.register_page(__name__, path="/info")

layout = dbc.Container(
    [
        html.H3("Definitions"),
        html.Hr(),
        html.B("Contributor"),
        html.Blockquote(
            [
                html.P(
                    """
                    An individual who has shared some software artifact or resource with an open source project.
                    In practice, we are able to attach multiple emails to a given contributor identity, so
                    a given contributor could make contributions under multiple emails.
                    It is reasonable to say that an individual is a contributor if they have made one-or-more contributions
                    to an open source project.
                    In 8Knot, we count someone as a 'contributor' if they make one or more 'contribution' as we define below.
                    """
                ),
            ]
        ),
        html.Hr(),
        html.B("Contribution"),
        html.Blockquote(
            [
                html.P(
                    """
                    A software artifact or resource that is shared with an open source project by some individual.
                    There is no explicit, agreed-upon ranking among contributions. Where appropriate, we leave that
                    to the discretion of the application user. There are, however, events that we do not consider
                    contributions because nothing is shared with the project.
                    """
                ),
                html.Br(),
                html.H5("Contributions that 8Knot counts in visualizations and metrics:"),
                html.Ul(
                    [
                        html.Li("Pull Requests: Create, Close, Merge, Review, Comment"),
                        html.Li("Issues: Create, Close, Comment"),
                        html.Li("Commits: Author, Commit"),
                    ]
                ),
                html.H5("Non-contributions (8Knot doesn't count these):"),
                html.Ul(
                    [
                        html.Li("Starring a project"),
                        html.Li("Forking a project"),
                        html.Li("Watching a project"),
                    ]
                ),
            ]
        ),
        html.Hr(),
        html.B("Contributor Recency"),
        html.Blockquote(
            [
                html.P(
                    """
                    Because open source projects are asynchronous it is useful to know, on aggregate, how many contributors
                    have made a contribution recently. Likewise, it is interesting to know how many previous contributors
                    have NOT made a contribution recently. We measure these populations by allowing the user to define the
                    following time ranges, and then counting the contributors whose contribution recency falls within the
                    respective ranges.
                    """
                ),
                html.Br(),
                html.H5("Contribution activity time-ranges:"),
                html.H6("T0---------T1---------T2--------->>"),
                html.Ul(
                    [
                        html.Li("T0: 'now'"),
                        html.Li("T1: recent past, e.g. 'six months ago'"),
                        html.Li("T2: further past, e.g. 'eighteen months ago'"),
                    ]
                ),
                html.H5("Contributor activity categories:"),
                html.Ul(
                    [
                        html.Li("Active: last seen between T0 and T1"),
                        html.Li("Drifting: last seen between T1 and T2"),
                        html.Li("Away: last seen no more recently than T2"),
                    ]
                ),
            ]
        ),
        html.Hr(),
        html.B("Contributor Consistency"),
        html.Blockquote(
            [
                html.P(
                    """
                    It is interesting to know how many contributors are 'fly-by,' creating an issue or a PR only once or a
                    few times, versus those 'repeat' contributors who make relatively many contributions. The application user can set this threshold
                    in order to count the population of contributors who fall into either category.
                    """
                ),
                html.Br(),
                html.H5("Contribution consistency threshold:"),
                html.Ul(
                    [
                        html.Li("N: number of contributions"),
                    ]
                ),
                html.H5("Contributor consistency categories:"),
                html.Ul(
                    [
                        html.Li("Fly-by: # contributions to the project < N"),
                        html.Li("Repeat: # contributions to the project >= N"),
                    ]
                ),
            ]
        ),
        html.Hr(),
        html.B("Staleness"),
        html.Blockquote(
            [
                html.P(
                    """
                    Some contributions have a 'lifespan' between when they are opened and when they are closed.
                    The 'lifespan' that a time-sensitive contribution to a project has can be very informative. If issues or pull requests are
                    open for a very long time, for instance, this can signal problems for a community. Only those who are
                    very familiar with a community can know how 'old' is a negative thing, however, and whether the 'age' of these
                    contributions is important to consider.
                    """
                ),
                html.P(
                    """
                    This is a close relative to contributor activity states defined above.
                    """
                ),
                html.Br(),
                html.H5("Time-open thresholds:"),
                html.H6("T0---------T1---------T2--------->>"),
                html.Ul(
                    [
                        html.Li("T0: 'now'"),
                        html.Li("T1: recent past, e.g. 'six months ago'"),
                        html.Li("T2: further past, e.g. 'eighteen months ago'"),
                    ]
                ),
                html.H5("Time-open staleness categories:"),
                html.Ul(
                    [
                        html.Li("Fresh: opened between T0 and T1, still open"),
                        html.Li("Staling: opened between T1 and T2, still open"),
                        html.Li("Stale: opened before T2, still open"),
                    ]
                ),
            ]
        ),
    ],
    fluid=True,
)
