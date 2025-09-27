from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil, os, uuid, pandas as pd
from .ingest import read_any
from .schema_infer import infer_schema, normalize
from .anomaly import flag_numeric_outliers
from .analysis import concentration
from .insights import simple_insights
from .storage import ensure_dir, write_csv, write_json
from .audit import new_audit, to_json

app = FastAPI(title="Analytical Pipeline POC")

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    group: str | None = Form(None),
    metric: str | None = Form(None),
    time_col: str | None = Form(None),
):
    run_id = str(uuid.uuid4())
    outdir = ensure_dir(f"outputs/{run_id}")

    tmp_path = os.path.join(outdir, file.filename)
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    df_raw, meta = read_any(tmp_path, None)
    schema = infer_schema(df_raw)
    time_col = time_col or schema["time_col"]
    df = normalize(df_raw, time_col)

    group_col = group or (schema["categorical_candidates"][0] if schema["categorical_candidates"] else None)
    metric_col = metric or (schema["numeric_candidates"][0] if schema["numeric_candidates"] else None)
    if not group_col or not metric_col:
        return JSONResponse({"error": "Could not infer group/metric", "schema": schema}, status_code=400)

    anomalies = flag_numeric_outliers(df)
    by_group_period, summary = concentration(df, group_col, metric_col, time_col)
    insights = simple_insights(summary, time_col or "_time")

    artifacts = {}
    artifacts["normalized"] = write_csv(df, os.path.join(outdir, "normalized.csv"))
    artifacts["anomalies"] = write_csv(anomalies, os.path.join(outdir, "anomalies.csv"))
    artifacts["by_group_period"] = write_csv(by_group_period, os.path.join(outdir, "concentration_by_group_period.csv"))
    artifacts["summary"] = write_csv(summary, os.path.join(outdir, "concentration_summary.csv"))

    xlsx_path = os.path.join(outdir, "outputs.xlsx")
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
        "input_file": file.filename,
    }, artifacts, meta)
    artifacts["audit"] = write_json(to_json(audit), os.path.join(outdir, "audit.json"))

    return {
        "run_id": run_id,
        "schema": schema,
        "group_col": group_col,
        "metric_col": metric_col,
        "time_col": time_col,
        "artifacts": artifacts,
        "insights": insights,
    }