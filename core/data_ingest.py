from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from dateutil import parser


# ------------------------------ LOADING ------------------------------ #

def load_any_table(file_like) -> pd.DataFrame:
    """
    Load CSV or Excel into a DataFrame with naive dtype inference.
    Accepts a path-like object or a file-like (e.g., Streamlit uploaded file).
    """
    name = getattr(file_like, "name", "").lower()
    if name.endswith(".csv"):
        return pd.read_csv(file_like)
    if name.endswith(".xls") or name.endswith(".xlsx"):
        return pd.read_excel(file_like)
    # Fall back: try CSV then Excel
    try:
        file_like.seek(0)
        return pd.read_csv(file_like)
    except Exception:
        file_like.seek(0)
        return pd.read_excel(file_like)


# ------------------------------ DATE / PERIOD COERCION ------------------------------ #

def _coerce_datetime_series(s: pd.Series) -> pd.Series:
    """
    Try hard to coerce to datetime. Handles objects/ints/strings.
    """
    if pd.api.types.is_datetime64_any_dtype(s):
        return pd.to_datetime(s, errors="coerce")
    # Observe mixed types; rely on pandas to parse, otherwise dateutil.
    try:
        return pd.to_datetime(s, errors="coerce", utc=False, infer_datetime_format=True)
    except Exception:
        return s.apply(lambda x: parser.parse(str(x)) if pd.notna(x) else pd.NaT)


def coerce_dates_and_periods(df: pd.DataFrame, time_col: str, period_grain: str) -> pd.DataFrame:
    """
    Ensure df[time_col] is datetime64 and add a 'period' column in a human friendly label.
    period_grain ∈ {'Quarter', 'Month', 'Year'}.
    """
    out = df.copy()
    out[time_col] = _coerce_datetime_series(out[time_col])
    out = out.dropna(subset=[time_col])
    out.sort_values(time_col, inplace=True)

    if period_grain == "Quarter":
        # Period like 'Q1-20'
        q = out[time_col].dt.to_period("Q")
        out["period"] = q.apply(lambda p: f"Q{p.quarter}-{str(p.year)[-2:]}")
    elif period_grain == "Month":
        out["period"] = out[time_col].dt.to_period("M").astype(str)
    elif period_grain == "Year":
        out["period"] = out[time_col].dt.year.astype(str)
    else:
        raise ValueError("period_grain must be one of: Quarter, Month, Year")

    return out


# ------------------------------ COLUMN GUESSING ------------------------------ #

@dataclass
class ColumnGuesses:
    time_index: int
    cat_index: int
    num_index: int


def guess_columns(df: pd.DataFrame) -> ColumnGuesses:
    """
    Heuristics to pre-select columns for the UI:
      - time: first datetime-like or a column name containing common date tokens
      - numeric: first numeric
      - categorical: first object/string that isn't the time column
    """
    cols = list(df.columns)
    time_idx = 0
    num_idx = 0
    cat_idx = 0

    # guess time
    date_tokens = {"date", "dt", "time", "timestamp", "period", "month", "quarter", "year"}
    for i, c in enumerate(cols):
        lc = str(c).lower()
        if any(tok in lc for tok in date_tokens):
            time_idx = i
            break
    else:
        # If none matched by name, look for datetime-like
        for i, c in enumerate(cols):
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                time_idx = i
                break

    # guess numeric
    for i, c in enumerate(cols):
        if pd.api.types.is_numeric_dtype(df[c]):
            num_idx = i
            break

    # guess categorical (object-ish and not the time col)
    for i, c in enumerate(cols):
        if i == time_idx:
            continue
        if df[c].dtype == "object" or pd.api.types.is_string_dtype(df[c]):
            cat_idx = i
            break

    return ColumnGuesses(time_index=time_idx, cat_index=cat_idx, num_index=num_idx)
