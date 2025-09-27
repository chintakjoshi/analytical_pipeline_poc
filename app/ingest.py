from __future__ import annotations
import pandas as pd, os
from .storage import file_sha256

def read_any(path: str, sheet=None) -> tuple[pd.DataFrame, dict]:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xls"]:
        if sheet is None:
            df = pd.read_excel(path, sheet_name=0)
        else:
            df = pd.read_excel(path, sheet_name=sheet)
    elif ext == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file: {ext}")
    meta = {
        "path": path,
        "sheet": sheet,
        "file_sha256": file_sha256(path),
        "n_rows": len(df),
        "n_cols": len(df.columns),
    }
    return df, meta