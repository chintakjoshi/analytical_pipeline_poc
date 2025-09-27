from __future__ import annotations
import argparse, os, uuid, pandas as pd
from .ingest import read_any
from .schema_infer import infer_schema, normalize
from .anomaly import flag_numeric_outliers
from .analysis import concentration
from .insights import simple_insights
from .storage import ensure_dir, write_parquet, write_csv, write_json
from .audit import new_audit, to_json

def main():
    p = argparse.ArgumentParser(description="POC analytical pipeline: concentration analysis")
    p.add_argument("--input", required=True)
    p.add_argument("--sheet", default=None)
    p.add_argument("--group", default=None)
    p.add_argument("--metric", default=None)
    p.add_argument("--time-col", default=None)
    p.add_argument("--outdir", default="outputs")
    p.add_argument("--excel-export", action="store_true")
    args = p.parse_args()

    outdir = ensure_dir(args.outdir)
    run_id = str(uuid.uuid4())

    df_raw, meta = read_any(args.input, args.sheet)
    schema = infer_schema(df_raw)
    time_col = args.time_col or schema["time_col"]
    df = normalize(df_raw, time_col)

    group_col = args.group or (schema["categorical_candidates"][0] if schema["categorical_candidates"] else None)
    metric_col = args.metric or (schema["numeric_candidates"][0] if schema["numeric_candidates"] else None)
    if not group_col or not metric_col:
        raise SystemExit(f"Could not infer group/metric.\nSchema: {schema}")

    anomalies = flag_numeric_outliers(df)
    by_group_period, summary = concentration(df, group_col, metric_col, time_col)
    insights = simple_insights(summary, time_col or "_time")

    artifacts = {}
    artifacts["normalized"] = write_parquet(df, os.path.join(outdir, "normalized.parquet"))
    artifacts["anomalies"] = write_csv(anomalies, os.path.join(outdir, "anomalies.csv"))
    artifacts["by_group_period"] = write_csv(by_group_period, os.path.join(outdir, "concentration_by_group_period.csv"))
    artifacts["summary"] = write_csv(summary, os.path.join(outdir, "concentration_summary.csv"))

    if args.excel_export:
        xlsx_path = os.path.join(outdir, "concentration_outputs.xlsx")
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xlw:
            df.to_excel(xlw, sheet_name="normalized", index=False)
            anomalies.to_excel(xlw, sheet_name="anomalies", index=False)
            by_group_period.to_excel(xlw, sheet_name="by_group_period", index=False)
            summary.to_excel(xlw, sheet_name="summary", index=False)
        artifacts["excel"] = xlsx_path

    audit = new_audit(run_id, {
        "group_col": group_col,
        "metric_col": metric_col,
        "time_col": time_col,
        "input": args.input,
        "sheet": args.sheet,
    }, artifacts, meta)
    artifacts["audit"] = write_json(to_json(audit), os.path.join(outdir, "audit.json"))

    print("=== Run Complete ===")
    print(f"Run ID: {run_id}")
    print(f"Inferred schema: {schema}")
    print(f"Group: {group_col} | Metric: {metric_col} | Time: {time_col}")
    print("Artifacts:")
    for k, v in artifacts.items():
        print(f" - {k}: {v}")
    if insights:
        print("Insights:")
        for s in insights:
            print(f" * {s}")

if __name__ == "__main__":
    main()