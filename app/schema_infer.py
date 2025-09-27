from __future__ import annotations
import pandas as pd, numpy as np, re
from typing import Optional

DATE_HINTS = re.compile(r"(date|period|month|quarter|year|yr|dt|time)", re.I)

def infer_schema(df: pd.DataFrame) -> dict:
    df_i = df.copy()
    date_candidates = []
    for c in df_i.columns:
        if DATE_HINTS.search(str(c)) or np.issubdtype(df_i[c].dtype, np.datetime64):
            date_candidates.append(c)
            try:
                df_i[c] = pd.to_datetime(df_i[c], errors="ignore")
            except Exception:
                pass

    numerics, categoricals = [], []
    for c in df_i.columns:
        s = df_i[c]
        if pd.api.types.is_numeric_dtype(s):
            numerics.append(c)
        elif s.dtype == "object" or pd.api.types.is_categorical_dtype(s):
            if s.nunique(dropna=True) <= max(1000, len(s) * 0.5):
                categoricals.append(c)

    time_col: Optional[str] = None
    dt_cols = [c for c in df_i.columns if pd.api.types.is_datetime64_any_dtype(df_i[c])]
    if dt_cols:
        time_col = dt_cols[0]
    elif date_candidates:
        for c in date_candidates:
            coerced = pd.to_datetime(df_i[c], errors="coerce")
            if coerced.notna().mean() > 0.7:
                df_i[c] = coerced
                time_col = c
                break

    return {
        "time_col": time_col,
        "numeric_candidates": numerics,
        "categorical_candidates": categoricals,
        "preview": df_i.head(5).to_dict(orient="records"),
    }

def normalize(df: pd.DataFrame, time_col: Optional[str]) -> pd.DataFrame:
    out = df.copy()
    if time_col and not pd.api.types.is_datetime64_any_dtype(out[time_col]):
        out[time_col] = pd.to_datetime(out[time_col], errors="coerce")
    return out