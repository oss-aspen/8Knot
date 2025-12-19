"""
Performance Benchmarks for Polars Migration

This script measures performance improvements from the Polars migration.
Run with: python -m benchmarks.polars_benchmark

Benchmarks:
1. DataFrame creation: Pandas vs Polars from raw data
2. Common operations: groupby, filter, sort
3. The specific anti-patterns we fixed
"""

import time
import numpy as np
import pandas as pd
import polars as pl
from typing import Callable
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """Result of a benchmark comparison."""

    name: str
    pandas_time: float
    polars_time: float

    @property
    def speedup(self) -> float:
        """Calculate speedup factor (higher is better for Polars)."""
        if self.polars_time == 0:
            return float("inf")
        return self.pandas_time / self.polars_time

    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Pandas: {self.pandas_time:.4f}s\n"
            f"  Polars: {self.polars_time:.4f}s\n"
            f"  Speedup: {self.speedup:.2f}x"
        )


def time_function(func: Callable, n_runs: int = 3) -> float:
    """Time a function, returning the average of n_runs."""
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        func()
        times.append(time.perf_counter() - start)
    return sum(times) / len(times)


def generate_test_data(n_rows: int = 100_000) -> dict:
    """Generate test data for benchmarks."""
    np.random.seed(42)
    return {
        "id": np.arange(n_rows),
        "category": np.random.choice(["A", "B", "C", "D", "E"], n_rows),
        "value": np.random.randn(n_rows) * 100,
        "count": np.random.randint(1, 100, n_rows),
        "created_at": pd.date_range("2020-01-01", periods=n_rows, freq="T"),
        "closed_at": pd.date_range("2020-01-01", periods=n_rows, freq="T")
        + pd.to_timedelta(np.random.randint(0, 30, n_rows), unit="D"),
    }


def benchmark_dataframe_creation(data: dict) -> BenchmarkResult:
    """Benchmark DataFrame creation."""

    def pandas_create():
        pd.DataFrame(data)

    def polars_create():
        pl.DataFrame(data)

    return BenchmarkResult(
        name="DataFrame Creation",
        pandas_time=time_function(pandas_create),
        polars_time=time_function(polars_create),
    )


def benchmark_groupby_agg(pd_df: pd.DataFrame, pl_df: pl.DataFrame) -> BenchmarkResult:
    """Benchmark groupby aggregation."""

    def pandas_groupby():
        pd_df.groupby("category").agg({"value": "sum", "count": "mean"})

    def polars_groupby():
        pl_df.group_by("category").agg([pl.col("value").sum(), pl.col("count").mean()])

    return BenchmarkResult(
        name="GroupBy Aggregation",
        pandas_time=time_function(pandas_groupby),
        polars_time=time_function(polars_groupby),
    )


def benchmark_filter_sort(pd_df: pd.DataFrame, pl_df: pl.DataFrame) -> BenchmarkResult:
    """Benchmark filtering and sorting."""

    def pandas_filter_sort():
        df = pd_df[pd_df["value"] > 0]
        df.sort_values("count", ascending=False)

    def polars_filter_sort():
        pl_df.filter(pl.col("value") > 0).sort("count", descending=True)

    return BenchmarkResult(
        name="Filter + Sort",
        pandas_time=time_function(pandas_filter_sort),
        polars_time=time_function(polars_filter_sort),
    )


def benchmark_conditional_column(pd_df: pd.DataFrame, pl_df: pl.DataFrame) -> BenchmarkResult:
    """Benchmark conditional column creation (like code_languages.py)."""

    def pandas_conditional():
        df = pd_df.copy()
        df.loc[df["category"] == "A", "value"] = df["count"]

    def polars_conditional():
        pl_df.with_columns(
            pl.when(pl.col("category") == "A").then(pl.col("count")).otherwise(pl.col("value")).alias("value")
        )

    return BenchmarkResult(
        name="Conditional Column (when/then)",
        pandas_time=time_function(pandas_conditional),
        polars_time=time_function(polars_conditional),
    )


def benchmark_vectorized_log(pd_df: pd.DataFrame, pl_df: pl.DataFrame) -> BenchmarkResult:
    """Benchmark vectorized log (like project_velocity.py fix)."""

    def pandas_log():
        # Old anti-pattern: df["value"].apply(lambda x: math.log(x) if x > 0 else 0)
        # New vectorized:
        np.where(pd_df["value"] > 0, np.log(pd_df["value"].abs()), 0)

    def polars_log():
        pl_df.select(pl.when(pl.col("value") > 0).then(pl.col("value").abs().log()).otherwise(0).alias("log_value"))

    return BenchmarkResult(
        name="Vectorized Log (anti-pattern fix)",
        pandas_time=time_function(pandas_log),
        polars_time=time_function(polars_log),
    )


def benchmark_cumsum_threshold(pd_df: pd.DataFrame, pl_df: pl.DataFrame) -> BenchmarkResult:
    """Benchmark cumsum + threshold finding (like lottery factor fix)."""
    threshold = pd_df["count"].sum() * 0.5

    def pandas_cumsum():
        cumsum = pd_df["count"].cumsum()
        np.searchsorted(cumsum.values, threshold, side="left")

    def polars_cumsum():
        cumsum = pl_df.select(pl.col("count").cum_sum())
        # Polars doesn't have searchsorted, but we can filter
        cumsum.filter(pl.col("count") >= threshold).head(1)

    return BenchmarkResult(
        name="Cumsum + Threshold (lottery factor)",
        pandas_time=time_function(pandas_cumsum),
        polars_time=time_function(polars_cumsum),
    )


def benchmark_open_count_vectorized(pd_df: pd.DataFrame, pl_df: pl.DataFrame) -> BenchmarkResult:
    """Benchmark open item counting (like issues_over_time.py fix)."""

    # Create date range for testing
    dates = pd.date_range("2020-01-15", periods=100, freq="D")

    def pandas_open_count():
        # The vectorized approach we implemented
        created = pd_df["created_at"].values
        closed = pd_df["closed_at"].values
        for date in dates[:10]:  # Sample 10 dates
            created_mask = created <= date
            still_open_mask = pd.isna(closed) | (closed > date)
            np.sum(created_mask & still_open_mask)

    def polars_open_count():
        # Polars approach
        for date in dates[:10]:  # Sample 10 dates
            pl_df.filter(
                (pl.col("created_at") <= date) & (pl.col("closed_at").is_null() | (pl.col("closed_at") > date))
            ).height

    return BenchmarkResult(
        name="Open Items Count (vectorized)",
        pandas_time=time_function(pandas_open_count),
        polars_time=time_function(polars_open_count),
    )


def run_all_benchmarks():
    """Run all benchmarks and print results."""
    print("=" * 60)
    print("POLARS MIGRATION PERFORMANCE BENCHMARKS")
    print("=" * 60)
    print()

    # Generate test data
    print("Generating test data (100,000 rows)...")
    data = generate_test_data(100_000)
    pd_df = pd.DataFrame(data)
    pl_df = pl.DataFrame(data)
    print()

    # Run benchmarks
    results = [
        benchmark_dataframe_creation(data),
        benchmark_groupby_agg(pd_df, pl_df),
        benchmark_filter_sort(pd_df, pl_df),
        benchmark_conditional_column(pd_df, pl_df),
        benchmark_vectorized_log(pd_df, pl_df),
        benchmark_cumsum_threshold(pd_df, pl_df),
        benchmark_open_count_vectorized(pd_df, pl_df),
    ]

    # Print results
    print("-" * 60)
    print("RESULTS")
    print("-" * 60)
    for result in results:
        print(result)
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    avg_speedup = sum(r.speedup for r in results) / len(results)
    max_speedup = max(results, key=lambda r: r.speedup)
    print(f"Average Speedup: {avg_speedup:.2f}x")
    print(f"Best Speedup: {max_speedup.name} ({max_speedup.speedup:.2f}x)")
    print()
    print("Recommendations:")
    for result in results:
        if result.speedup > 2:
            print(f"  ✅ {result.name}: {result.speedup:.2f}x faster with Polars")
        elif result.speedup > 1:
            print(f"  ⚡ {result.name}: {result.speedup:.2f}x faster with Polars")
        else:
            print(f"  ⚠️  {result.name}: Pandas faster ({1/result.speedup:.2f}x)")


if __name__ == "__main__":
    run_all_benchmarks()
