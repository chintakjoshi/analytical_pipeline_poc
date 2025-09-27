from __future__ import annotations
import pandas as pd, numpy as np

def _bucket_by_cumshare(gdf: pd.DataFrame, value_col: str) -> pd.DataFrame:
    gdf = gdf.sort_values(value_col, ascending=False).reset_index(drop=True)
    total = gdf[value_col].sum()
    gdf["cum_share"] = gdf[value_col].cumsum() / total if total else 0
    def label_row(c):
        if c <= 0.10: return "Top 10%"
        if c <= 0.20: return "Top 20%"
        if c <= 0.50: return "Top 50%"
        return "Remainder"
    gdf["bucket"] = gdf["cum_share"].apply(label_row)
    return gdf

def concentration(df: pd.DataFrame, group_col: str, value_col: str, time_col: str | None):
    if time_col is None:
        tmp = df.copy()
        tmp["_time"] = "ALL"
        time_col = "_time"
    else:
        tmp = df.copy()
    grouped = tmp.groupby([time_col, group_col], dropna=False, as_index=False)[value_col].sum()
    pieces = []
    for period, g in grouped.groupby(time_col):
        pieces.append(_bucket_by_cumshare(g, value_col).assign(**{time_col: period}))
    by_group_period = pd.concat(pieces, ignore_index=True)
    summary = by_group_period.groupby([time_col, "bucket"], as_index=False).agg(
        total_metric=(value_col, "sum"),
        n_groups=(group_col, "nunique"),
    )
    summary["period_total"] = summary.groupby(time_col)["total_metric"].transform("sum")
    summary["share_of_period"] = (summary["total_metric"] / summary["period_total"]).fillna(0.0)
    return by_group_period, summary