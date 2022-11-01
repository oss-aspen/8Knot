import datetime as dt


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
    period = "M12"

    # graph input values based on date interval selection
    if interval == 86400000 or interval == "D":  # if statement for days
        x_r = [str(today - dt.timedelta(weeks=4)), str(today)]
        x_name = "Day"
        hover = "Day: %{x|%b %d, %Y}"
        period = 86400000
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
    else:
        period = "M12"

    return x_r, x_name, hover, period
