from __future__ import annotations
import io
from typing import Optional
import numpy as np
import pandas as pd

def format_money_df(df: pd.DataFrame, fmt: str = ",.2f") -> pd.DataFrame:
    """
    Return a *string-formatted* copy of df where all numeric cells are formatted with `fmt`.
    Leaves index as-is. Useful for Streamlit's dataframe (readable like the screenshot).
    """
    if df.empty:
        return df.copy()

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    out = df.copy()
    for c in numeric_cols:
        out[c] = out[c].apply(lambda x: (format(x, fmt) if pd.notna(x) else ""))
    return out


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a DataFrame to an in-memory .xlsx and return bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="concentration", index=True)
    buf.seek(0)
    return buf.read()