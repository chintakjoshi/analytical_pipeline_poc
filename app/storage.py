from __future__ import annotations
import os, json, hashlib, pathlib, pandas as pd

def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_parquet(df: pd.DataFrame, path: str) -> str:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(path, index=False)
        return path
    except Exception:
        # fallback to CSV
        csv_path = str(path).replace(".parquet", ".csv")
        df.to_csv(csv_path, index=False)
        return csv_path

def write_csv(df: pd.DataFrame, path: str) -> str:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path

def write_json(obj, path: str) -> str:
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)
    return path