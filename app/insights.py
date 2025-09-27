from __future__ import annotations
import pandas as pd

def simple_insights(summary: pd.DataFrame, time_col: str) -> list[str]:
    out = []
    for period, g in summary.groupby(time_col):
        row = g[g["bucket"]=="Top 10%"]
        if not row.empty and row["share_of_period"].iloc[0] > 0.6:
            out.append(f"{period}: Highly concentrated — Top 10% contributes {row['share_of_period'].iloc[0]:.1%}.")
        row = g[g["bucket"]=="Remainder"]
        if not row.empty and row["share_of_period"].iloc[0] < 0.2:
            out.append(f"{period}: Long tail small — Remainder contributes {row['share_of_period'].iloc[0]:.1%}.")
    return out