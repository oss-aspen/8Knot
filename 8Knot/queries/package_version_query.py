import logging
import cache_manager.cache_facade as cf
from app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_kwargs={"max_retries": 5},
    retry_jitter=True,
)
def package_version_query(self, repos):
    """
    (Worker Query)
    Executes SQL query against Augur database for package dependency versioning data.

    Args:
    -----
        repos ([int]): repos that SQL query is executed on.

    Returns:
    --------
        dict: Results from SQL query, interpreted from pd.to_dict('records')

    """
    logging.warning(f"{package_version_query.__name__} COLLECTION - START")

    if len(repos) == 0:
        return None

    query_string = """
                SELECT
                    rdl.repo_id as id,
                    rdl.name,
                    rdl.current_release_date,
                    rdl.latest_release_date,
                    rdl.libyear
                FROM
                    repo_deps_libyear rdl
                WHERE
                    repo_id IN %s
                    AND
                    (rdl.repo_id, rdl.data_collection_date) IN (
                        SELECT DISTINCT ON (repo_id)
                            repo_id, data_collection_date
                        FROM repo_deps_libyear
                        WHERE
                            repo_id IN %s
                        ORDER BY repo_id, data_collection_date DESC
                    ) AND
                    rdl.libyear >= 0
                """

    func_name = package_version_query.__name__

    # raises Exception on failure. Returns nothing.
    cf.caching_wrapper(func_name=func_name, query=query_string, repolist=repos, n_repolist_uses=2)

    logging.warning(f"{package_version_query.__name__} COLLECTION - END")
