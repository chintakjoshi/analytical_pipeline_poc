from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


def _top_k_count(n: int, pct: int) -> int:
    """Number of groups to include for a given percentage of count."""
    if n <= 0:
        return 0
    k = math.ceil(n * (pct / 100.0))
    return max(1, min(n, k))


def _sum_top_groups_for_period(
    g: pd.DataFrame,
    group_col: str,
    value_col: str,
    pct: int,
    ascending: bool,
) -> Tuple[float, int]:
    """
    For one period `g`, rank groups by aggregated value and take top `pct`% by COUNT of groups.
    Return (sum_value_of_selected_groups, number_of_groups_selected).
    """
    # aggregate by group first
    agg = g.groupby(group_col, dropna=False, observed=True)[value_col].sum().reset_index()

    # order and choose the slice
    agg_sorted = agg.sort_values(value_col, ascending=ascending, kind="mergesort")
    n_groups = len(agg_sorted)
    k = _top_k_count(n_groups, pct)
    head = agg_sorted.head(k)
    return float(head[value_col].sum()), int(k)


def concentration_by_period(
    df: pd.DataFrame,
    period_col: str,
    group_col: str,
    value_col: str,
    percent_buckets: Iterable[int] = (10, 20, 50),
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Compute concentration by period. Each (row, column) is the sum of `value_col` contributed by the
    top X% of groups (by COUNT) for that period. The row labels include the chosen count per column,
    e.g., 'Top 10% (81)' like in the screenshot.

    Returns a wide dataframe with:
      - rows: 'Top {pct}% (N)', for each pct in percent_buckets, plus a 'Total' row
      - cols: unique periods
    """
    if df.empty:
        return pd.DataFrame()

    # Sum total per period (for the Total row)
    total_per_period = df.groupby(period_col, observed=True)[value_col].sum().sort_index()

    # Pre-compute N per period so we can annotate "(N)" in the row index
    n_groups_per_period = (
        df.groupby(period_col, observed=True)[group_col].nunique(dropna=False).astype(int)
    )

    # Work period by period
    periods = total_per_period.index.tolist()
    result_data: Dict[str, List[float]] = {str(p): [] for p in periods}
    counts_for_rows: Dict[int, List[int]] = {pct: [] for pct in percent_buckets}

    # For each bucket, compute the sum for each period
    for pct in percent_buckets:
        for p in periods:
            g = df.loc[df[period_col] == p, [group_col, value_col]]
            s, k = _sum_top_groups_for_period(
                g, group_col=group_col, value_col=value_col, pct=pct, ascending=ascending
            )
            result_data[str(p)].append(s)
            counts_for_rows[pct].append(k)

    # Build index labels like 'Top 10% (81)' using the per-period k.
    # The number in parentheses in the screenshot appears to correspond to *one* period,
    # but a more informative multi-period table can show "(k varies)" if different.
    # We’ll derive a compact label: use the **median** k across periods for readability.
    index_labels: List[str] = []
    for pct in percent_buckets:
        ks = counts_for_rows[pct]
        if len(ks) == 0:
            label = f"Top {pct}% (0)"
        else:
            median_k = int(np.median(ks))
            label = f"Top {pct}% ({median_k})"
        index_labels.append(label)

    # Assemble wide frame for Top% rows
    top_frame = pd.DataFrame(result_data, index=index_labels)

    # Append Total row
    total_row = pd.DataFrame([total_per_period.values], index=["Total"], columns=[str(p) for p in periods])

    out = pd.concat([top_frame, total_row], axis=0)
    # Ensure consistent column order
    out = out[[str(p) for p in periods]]
    return out
