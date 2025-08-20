import datetime as dt

# list of graph color hex
color_seq = [
    "#B5B682",  # sage
    "#c0bc5d",  # citron (yellow-ish)
    "#6C8975",  # reseda green
    "#D9AE8E",  # buff (pale pink)
    "#FFBF51",  # xanthous (orange-ish)
    "#C7A5A5",  # rosy brown
]

# Baby Blue color scale for graph gradients
baby_blue = [
    "#F0F9FF",  # Baby Blue 100 - very light
    "#E0F2FE",  # Baby Blue 200 - light
    "#BAE6FD",  # Baby Blue 300 - medium light
    "#7DD3FC",  # Baby Blue 400 - light blue
    "#38BDF8",  # Baby Blue 500 - main baby blue
    "#0EA5E9",  # Baby Blue 600 - medium dark
    "#0284C7",  # Baby Blue 700 - dark
    "#0369A1",  # Baby Blue 800 - very dark
    "#F7B009",  # Yellow 500 - main yellow
    "#FEDF89",  # Yellow 200 - light yellow
    "#B54708",  # Yellow 700 - dark yellow



def get_graph_time_values(interval):
    """
    Utility needed in page visualizations-
    when the user inputs an 'interval', they're wanting to view
    data in some time window. This function converts that
    'interval' value to the necessary Plotly figure update values.

    Args:
    -----
        interval (str | int): How long between time bins, user selected.

    Returns:
    --------
        x_r ([str]): Time-bin strings.
        x_name (str): Name of bin-duration.
        hover (str): String-structure for graph to print on mouse-hover.
        period (str): How long selected time bin is.
    """
    today = dt.date.today()
    x_r = None
    x_name = "Year"
    hover = "Year: %{x|%Y}"
    period = "M12"  # dtick values must be in millisecond or M format

    # graph input values based on date interval selection
    if interval == 86400000 or interval == "D":  # if statement for days
        x_r = [str(today - dt.timedelta(weeks=4)), str(today)]
        x_name = "Day"
        hover = "Day: %{x|%b %d, %Y}"
        period = 86400000 * 2
    elif interval == 604800000 or interval == "W":  # if statmement for weeks
        x_r = [str(today - dt.timedelta(weeks=30)), str(today)]
        x_name = "Week"
        hover = "Week: %{x|%b %d, %Y}"
        period = 1814400000
    elif interval == "M" or interval == "M1":  # if statement for months
        x_r = [str(today - dt.timedelta(weeks=104)), str(today)]
        x_name = "Month"
        hover = "Month: %{x|%b %Y}"
        period = "M3"
    elif interval == "M3":  # if statement for quarter
        x_r = [str(today - dt.timedelta(weeks=312)), str(today)]
        x_name = "Quarter"
        hover = "Quarter: %{x}"
        period = "M6"
    elif interval == "M6":  # if statement for half a year
        x_r = [str(today - dt.timedelta(weeks=624)), str(today)]
        x_name = "Semiannual"
        hover = "Semiannual: %{x}"
        period = "M12"
    else:
        period = "M12"

    return x_r, x_name, hover, period
