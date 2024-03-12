def contributors_df_action_naming(df):
    """Renames verbs in 'Action' column

    Args:
        df (pd.DataFrame): contributors code table

    Returns:
        pd.DataFrame: processed dataframe
    """
    df = df.copy()
    # update column values
    df.loc[df["action"] == "pull_request_open", "action"] = "PR Opened"
    df.loc[df["action"] == "pull_request_comment", "action"] = "PR Comment"
    df.loc[df["action"] == "pull_request_closed", "action"] = "PR Closed"
    df.loc[df["action"] == "pull_request_merged", "action"] = "PR Merged"
    df.loc[df["action"] == "pull_request_review_COMMENTED", "action"] = "PR Review"
    df.loc[df["action"] == "pull_request_review_APPROVED", "action"] = "PR Review"
    df.loc[df["action"] == "pull_request_review_CHANGES_REQUESTED", "action"] = "PR Review"
    df.loc[df["action"] == "pull_request_review_DISMISSED", "action"] = "PR Review"
    df.loc[df["action"] == "issue_opened", "action"] = "Issue Opened"
    df.loc[df["action"] == "issue_closed", "action"] = "Issue Closed"
    df.loc[df["action"] == "issue_comment", "action"] = "Issue Comment"
    df.loc[df["action"] == "commit", "action"] = "Commit"
    df["cntrb_id"] = df["cntrb_id"].astype(str)  # contributor ids to strings
    df.rename(columns={"action": "Action"}, inplace=True)
    return df


def cntrb_per_file(df):
    # pandas column and format updates
    df["cntrb_ids"] = df["cntrb_ids"].str.split(",")
    df["reviewer_ids"] = df["reviewer_ids"].str.split(",")
    df = df.reset_index()
    df.drop("index", axis=1, inplace=True)
    return df
