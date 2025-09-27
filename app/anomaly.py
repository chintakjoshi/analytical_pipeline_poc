from __future__ import annotations
import pandas as pd, numpy as np

def flag_numeric_outliers(df: pd.DataFrame, z=3.5) -> pd.DataFrame:
    flags = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            series = df[col].astype(float)
            mu, sigma = series.mean(), series.std(ddof=1) if series.count() > 1 else 0
            if sigma == 0 or np.isnan(sigma):
                continue
            zscores = (series - mu) / sigma
            mask = zscores.abs() >= z
            if mask.any():
                flagged = df.loc[mask, [col]].copy()
                flagged["metric"] = col
                flagged["zscore"] = zscores[mask]
                flags.append(flagged.reset_index().rename(columns={"index": "row_index"}))
    return pd.concat(flags, ignore_index=True) if flags else pd.DataFrame(columns=["row_index","metric","zscore"])