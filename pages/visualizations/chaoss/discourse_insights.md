Overview of /explorer/pages/visualizations/chaoss/discourse_insights.py:
This visualization gives the count of pull requests and issues per discourse act over time.

Parameters taken : Interval(Day, Week, Month, Year)
Methods followed:
Method 1: Computing the discourse counts within the python script
1. The postgreSQL query used: 
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
2. The above query is used to get the information of pull requests and messages based on the data_collection_date from discourse_insights.
3. The query is then read into pandas dataframe.
4. Unique pull request and issue id's are then grabbed per discourse act individually.
5. All the pull request and issues are then grouped together to form a histogram based on the interval(day, week, month, year)
Method 2: Computing the discourse counts within the postgreSQL query and using it directly in the python script
1. The postgreSQL query used:
select repo_id, discourse_act, EXTRACT ( YEAR FROM msg_timestamp), count(*) as discourse_counts
from 
(
SELECT
	prmr.repo_id repo_id,
	prmr.msg_id,
	di.discourse_act,
	msg.msg_timestamp as msg_timestamp, 
	max(di.data_collection_date) as max_date,
	EXTRACT ( YEAR FROM MAX ( di.data_collection_date )) as year,
	COUNT ( * ) OVER ( PARTITION BY prmr.repo_id, discourse_act, prmr.msg_id, EXTRACT ( YEAR FROM MAX ( di.data_collection_date ))) discourse_counts 
FROM
	augur_data.pull_request_message_ref prmr,
	augur_data.discourse_insights di,
	augur_data.message msg 
WHERE
	prmr.msg_id = di.msg_id 
	AND msg.msg_id = prmr.msg_id 
	AND prmr.repo_id = 25457
Group by 1,2,3,4
	UNION
SELECT
	imr.repo_id repo_id,
	imr.msg_id,
	di.discourse_act,
		msg.msg_timestamp, 
	max(di.data_collection_date) as max_date, 
	EXTRACT ( YEAR FROM MAX ( di.data_collection_date)) as year, 
	COUNT ( * ) OVER ( PARTITION BY imr.repo_id, discourse_act, imr.msg_id, EXTRACT ( YEAR FROM MAX ( di.data_collection_date )) ) discourse_counts 
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
GROUP BY 1,2,3,4
) a 
group by 1,2,3
order by a.repo_id, date_part, discourse_act;
2. Parameters taken for the query: interval(day, week, month, year) and repo_id using which results are obtained dynamically.
3. Since the entire grouping is done within the sql query itself, only thing that needs to be done is directly obtain them for our visualization.
4. The SQL query result is written to a pandas dataframe(df) and the discourse counts can be obtained directly using df['discourse_counts'].
5. All the pull request and issues are then grouped together to form a histogram based on the interval(day, week, month, year).

Questions I had:
1. Since the expected result from this visualization is to obtain the pull request and issue counts per day, week, month or year, is it ideal to consider
the max(data_collection_date) from discourse_insights since the discourse_analysis_worker collects data daily which means we will get the visualization
only for today if we choose max_date.
2. If we choose Method 2 where the entire computation is done within the SQL query and we are providing the interval as the input parameter to the query,
the interval variable takes a different value which is in milliseconds i.e
                                                    id = "issue-time-interval",
                                                      options = [
                                                            {"label" : "Day", "value" : 86400000},
                                                            {"label" : "Week", "value" : 60480000},
                                                            {"label" : "Month", "value" : "M1"},
                                                            {"label" : "Year", "value" : "M12"},
                                                      ],
from line 97 of discourse_insights.py. which means if you're selecting day in the radio button the sql query will take it's value which is 86400000 instead of 'day'.
The SQL query will not provide the correct results in this case. Moreover Dash library is using different date terminology compared to SQL.
For example, SQL query grabs only the month if you're extracting month from timestamp whereas Dash grabs the month and year when you want to visualize the data based on month.
I found Method 2 more ideal due to aptness of the SQL query but the issue is with how we'll be properly translating the interval between SQL and Dash(Python).
3. I wanted to know more get_graph_time_values function and how the data is returned.
4. Currently I've directly exposed the database credentials and SQL query in the python script but while referring other visualization scripts I noticed
the input type as "data" which I assume is where data(SQL output) can be provided. I wanted to know more about the 'Data' type in Input of Dash Callbacks.
