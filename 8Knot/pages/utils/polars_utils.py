"""
Polars utilities for 8Knot.

This module provides the adapter layer for the "Polars Core, Pandas Edge" architecture:
- Core data processing uses Polars for 2-10x performance improvements
- Visualization boundary uses Pandas for Plotly/Dash compatibility

Architecture:
    Database → Query Layer (Polars) → Processing (Polars) → Visualization (Pandas → Plotly)

Usage:
    from pages.utils.polars_utils import to_polars, to_pandas, process_with_polars

    # Simple conversion
    pl_df = to_polars(pandas_df)
    result = to_pandas(polars_df)

    # Process with automatic conversion
    def my_processor(pl_df):
        return pl_df.filter(pl.col("x") > 0).group_by("category").agg(pl.col("value").sum())

    result = process_with_polars(pandas_df, my_processor)  # Returns Pandas DataFrame
"""

from typing import Callable, Union

import pandas as pd
import polars as pl

# Type alias for DataFrame compatibility
DataFrameLike = Union[pd.DataFrame, pl.DataFrame]


def to_polars(df: pd.DataFrame) -> pl.DataFrame:
    """
    Convert Pandas DataFrame to Polars for high-performance processing.

    Uses Arrow interchange for near zero-copy conversion when possible.

    Args:
        df: Input Pandas DataFrame

    Returns:
        Polars DataFrame ready for processing
    """
    return pl.from_pandas(df)


def to_pandas(df: pl.DataFrame) -> pd.DataFrame:
    """
    Convert Polars DataFrame to Pandas for visualization layer.

    This should be called at the visualization boundary, right before
    passing data to Plotly/Dash components.

    Args:
        df: Input Polars DataFrame

    Returns:
        Pandas DataFrame ready for Plotly/Dash
    """
    return df.to_pandas()


def process_with_polars(
    df: pd.DataFrame,
    processor: Callable[[pl.DataFrame], pl.DataFrame],
) -> pd.DataFrame:
    """
    Process a Pandas DataFrame with Polars and return Pandas.

    This is a convenience wrapper that handles the Pandas → Polars → Pandas
    conversion automatically. Use this when you want to leverage Polars
    performance while maintaining Pandas compatibility at boundaries.

    Args:
        df: Input Pandas DataFrame
        processor: Function that takes a Polars DataFrame and returns a Polars DataFrame

    Returns:
        Pandas DataFrame (result of processing)

    Example:
        def aggregate_by_category(pl_df: pl.DataFrame) -> pl.DataFrame:
            return (
                pl_df.lazy()
                .filter(pl.col("status") == "active")
                .group_by("category")
                .agg(pl.col("value").sum())
                .collect()
            )

        result = process_with_polars(pandas_df, aggregate_by_category)
        # result is a Pandas DataFrame ready for Plotly
    """
    pl_df = to_polars(df)
    result = processor(pl_df)
    return to_pandas(result)


def lazy_process(
    df: pd.DataFrame,
    processor: Callable[[pl.LazyFrame], pl.LazyFrame],
) -> pd.DataFrame:
    """
    Process a Pandas DataFrame with Polars lazy evaluation.

    Lazy evaluation allows Polars to optimize the entire query plan
    before execution, potentially resulting in significant speedups.

    Args:
        df: Input Pandas DataFrame
        processor: Function that takes a Polars LazyFrame and returns a LazyFrame

    Returns:
        Pandas DataFrame (result of processing)

    Example:
        def complex_aggregation(lf: pl.LazyFrame) -> pl.LazyFrame:
            return (
                lf.filter(pl.col("value") > 0)
                .with_columns(pl.col("date").dt.month().alias("month"))
                .group_by("month")
                .agg([
                    pl.col("value").sum().alias("total"),
                    pl.col("value").mean().alias("avg"),
                ])
            )

        result = lazy_process(pandas_df, complex_aggregation)
    """
    pl_df = to_polars(df)
    lazy_result = processor(pl_df.lazy())
    return to_pandas(lazy_result.collect())


# Common Polars expressions for reuse
class Expressions:
    """
    Common Polars expressions used across visualizations.

    These are pre-built expression patterns that can be reused
    to ensure consistency and avoid duplication.
    """

    @staticmethod
    def is_open_at_date(
        date,
        created_col: str = "created_at",
        closed_col: str = "closed_at",
    ) -> pl.Expr:
        """
        Expression to check if an item is open at a given date.

        An item is open if: created_at <= date AND (closed_at > date OR closed_at is null)
        """
        return (pl.col(created_col) <= date) & (pl.col(closed_col).is_null() | (pl.col(closed_col) > date))

    @staticmethod
    def safe_log(col: str, alias: str = None) -> pl.Expr:
        """
        Safe logarithm that handles zero values.

        Returns 0 for zero values, log(x) otherwise.
        """
        expr = pl.when(pl.col(col) != 0).then(pl.col(col).log()).otherwise(0)
        return expr.alias(alias) if alias else expr

    @staticmethod
    def truncate_to_period(col: str, interval: str) -> pl.Expr:
        """
        Truncate datetime column to a period (day, week, month, year).

        Args:
            col: Column name
            interval: "D", "W", "M", or "Y"

        Returns:
            Polars expression
        """
        interval_map = {"D": "1d", "W": "1w", "M": "1mo", "Y": "1y"}
        polars_interval = interval_map.get(interval, "1mo")
        return pl.col(col).dt.truncate(polars_interval)

    @staticmethod
    def to_utc_datetime(col: str) -> pl.Expr:
        """Convert a column to UTC datetime."""
        return pl.col(col).cast(pl.Datetime("us", "UTC"))

    @staticmethod
    def count_in_range(
        date,
        created_col: str = "created_at",
        closed_col: str = "closed_at",
    ) -> int:
        """
        Count items open at a specific date.

        This is a helper for use with filter operations.
        """
        return (pl.col(created_col) <= date) & (pl.col(closed_col).is_null() | (pl.col(closed_col) > date))


# Lazy evaluation helpers for complex aggregations
class LazyPatterns:
    """
    Common lazy evaluation patterns for Polars.

    Lazy evaluation allows Polars to optimize the entire query plan
    before execution. Use these patterns for complex multi-step operations.
    """

    @staticmethod
    def group_count_by_period(
        df: pl.DataFrame,
        date_col: str,
        interval: str,
        count_col: str = None,
        unique: bool = False,
    ) -> pl.DataFrame:
        """
        Group by time period and count (optionally unique values).

        Args:
            df: Polars DataFrame
            date_col: Column to use for grouping
            interval: "D", "W", "M", or "Y"
            count_col: Column to count (if None, counts rows)
            unique: If True, count unique values

        Returns:
            Aggregated DataFrame

        Example:
            # Count unique commits per month
            result = LazyPatterns.group_count_by_period(
                df, "created_at", "M", count_col="commit_hash", unique=True
            )
        """
        interval_map = {"D": "1d", "W": "1w", "M": "1mo", "Y": "1y"}
        polars_interval = interval_map.get(interval, "1mo")

        lf = df.lazy().with_columns(pl.col(date_col).dt.truncate(polars_interval).alias("_period"))

        if count_col:
            if unique:
                agg_expr = pl.col(count_col).n_unique().alias("count")
            else:
                agg_expr = pl.col(count_col).count().alias("count")
        else:
            agg_expr = pl.len().alias("count")

        return lf.group_by("_period").agg(agg_expr).sort("_period").collect()

    @staticmethod
    def filter_and_aggregate(
        df: pl.DataFrame,
        filter_expr: pl.Expr,
        group_by: Union[str, list],
        agg_exprs: list,
    ) -> pl.DataFrame:
        """
        Filter, group, and aggregate in one optimized operation.

        Args:
            df: Polars DataFrame
            filter_expr: Polars filter expression
            group_by: Column(s) to group by
            agg_exprs: List of aggregation expressions

        Returns:
            Aggregated DataFrame

        Example:
            result = LazyPatterns.filter_and_aggregate(
                df,
                filter_expr=pl.col("status") == "active",
                group_by="category",
                agg_exprs=[pl.col("value").sum(), pl.col("value").mean()],
            )
        """
        return df.lazy().filter(filter_expr).group_by(group_by).agg(agg_exprs).collect()

    @staticmethod
    def cumsum_threshold_search(
        df: pl.DataFrame,
        value_col: str,
        threshold: float,
    ) -> int:
        """
        Find the number of rows needed to reach a cumulative sum threshold.

        This is a vectorized replacement for iterrows() loops that calculate
        cumulative sums until a threshold is reached.

        Args:
            df: Polars DataFrame (sorted by the column of interest)
            value_col: Column to cumsum
            threshold: Target threshold

        Returns:
            Number of rows needed to reach threshold

        Example:
            # Find how many top contributors account for 80% of contributions
            df_sorted = df.sort("contributions", descending=True)
            n_rows = LazyPatterns.cumsum_threshold_search(
                df_sorted, "contributions", total_contributions * 0.8
            )
        """
        cumsum = df.select(pl.col(value_col).cum_sum())[value_col]
        # Find first index where cumsum >= threshold
        indices = cumsum.to_numpy() >= threshold
        if indices.any():
            return int(indices.argmax()) + 1
        return len(df)
