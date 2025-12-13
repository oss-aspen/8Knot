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
    def count_open_at_date(
        created_col: str = "created_at",
        closed_col: str = "closed_at",
    ) -> pl.Expr:
        """
        Expression to check if an item is open at a given date.

        An item is open if: created_at <= date AND (closed_at > date OR closed_at is null)
        """
        # This is a template - actual date comparison needs to be done in context
        return (pl.col(created_col).is_not_null()) & (
            pl.col(closed_col).is_null() | (pl.col(closed_col) > pl.col(created_col))
        )

    @staticmethod
    def safe_log(col: str) -> pl.Expr:
        """
        Safe logarithm that handles zero values.

        Returns 0 for zero values, log(x) otherwise.
        """
        return pl.when(pl.col(col) != 0).then(pl.col(col).log()).otherwise(0)
