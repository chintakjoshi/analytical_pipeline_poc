# Analytical Pipeline POC (Concentration Analysis + API)

This project is a lightweight proof-of-concept for an **analytical data pipeline**.  
It ingests Excel/CSV financial data, infers schema automatically, normalizes columns, detects anomalies, runs a **concentration analysis** (Top 10/20/50% buckets per period), and exports results.  

It can be used either as a **CLI tool** or as a **FastAPI service**.

---

## ✨ Features
- Upload Excel/CSV input files
- Automatic schema inference (categorical, numeric, and time columns)
- Normalization of dates and datatypes
- Outlier detection (z-score–based)
- Concentration analysis: cumulative shares, Top 10/20/50% buckets
- Insights surfaced (high concentration, long tail shrinkage, etc.)
- Full audit log: lineage, params, file hashes
- Export outputs to CSV and Excel
- REST API for programmatic access

---

## 🚀 Setup

### Local Environment
```bash
git clone <this-repo>
cd analytical-pipeline-poc
python -m venv .venv
. .venv/Scripts/activate      # Windows
# or: source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### Docker
```bash
docker build -t pipeline-poc .
docker run --rm -p 8000:8000 -v "$PWD:/work" pipeline-poc
```

---

## 🔧 Usage

### CLI
Run pipeline on sample data:

```bash
python -m app.cli --input data/sample.xlsx --outdir outputs
```

Explicit column selection:

```bash
python -m app.cli --input data/sample.xlsx   --group Customer --metric Revenue --time-col Period   --outdir outputs --excel-export
```

Artifacts will be written to `outputs/`:
- `normalized.csv`
- `anomalies.csv`
- `concentration_by_group_period.csv`
- `concentration_summary.csv`
- `outputs.xlsx`
- `audit.json`

---

### API

Start the FastAPI server:

```bash
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Upload a file:

#### PowerShell (Windows):
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/analyze" -Method POST `
  -Form @{ file = Get-Item "data/sample.xlsx" }
```

#### Real curl:
```powershell
& curl.exe -X POST "http://localhost:8000/analyze" -F "file=@data/sample.xlsx"
```

#### Python client:
```python
import requests
files = {"file": open("data/sample.xlsx", "rb")}
resp = requests.post("http://localhost:8000/analyze", files=files)
print(resp.json())
```

Response JSON includes schema, chosen columns, artifact paths, and insights.

---

## 🧪 Tests
```bash
pytest -q
```

---

## ⚙️ Design Notes
- Modular pipeline: `ingest` → `schema_infer` → `anomaly` → `analysis` → `storage` → `audit`
- Stateless CLI/API: outputs everything into `outputs/<run_id>/`
- Schema inference is dynamic, no hardcoding
- Artifacts + `audit.json` provide full lineage & reproducibility
- Scaling path: swap Pandas → Polars/DuckDB/Spark; add dbt for transformations; orchestrate with Prefect/Dagster

---

## ✅ Success Criteria
- **Organized** workflows with modular design
- **Standardized** artifact outputs
- **Documented** transformations (`audit.json`)
- **Extensible** to larger-scale engines and orchestration
