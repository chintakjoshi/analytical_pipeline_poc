import io
from datetime import datetime
from typing import List
import pandas as pd
import streamlit as st
from core.data_ingest import load_any_table, coerce_dates_and_periods, guess_columns
from core.concentration import concentration_by_period
from core.utils import format_money_df, to_excel_bytes

# ------------------------------ PAGE CONFIG ------------------------------ #
st.set_page_config(
    page_title="Concentration Analysis POC",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Concentration Analysis (POC)")

# ------------------------------ SIDEBAR ------------------------------ #
st.sidebar.header("⚙️ Analysis Settings")

uploaded = st.sidebar.file_uploader(
    "Upload a CSV or Excel file", type=["csv", "xls", "xlsx"]
)

if uploaded is None:
    st.info("⬅️ Upload a dataset in the sidebar to get started")
    st.stop()

# Load data
try:
    df_raw = load_any_table(uploaded)
except Exception as e:
    st.error(f"❌ Could not read the file: {e}")
    st.stop()

if df_raw.empty:
    st.error("❌ The file appears to have no rows.")
    st.stop()

st.success(f"✅ Loaded {len(df_raw):,} rows × {df_raw.shape[1]} columns")

# Preview sample
st.subheader("🔎 Data Preview")
st.dataframe(df_raw.head(10), use_container_width=True)

# ------------------------------ COLUMN SELECTION ------------------------------ #
guesses = guess_columns(df_raw)

with st.sidebar.expander("1️⃣ Select Columns", expanded=True):
    time_col = st.selectbox(
        "Time column",
        options=df_raw.columns.tolist(),
        index=guesses.time_index,
    )
    cat_col = st.selectbox(
        "Categorical column (group by)",
        options=df_raw.columns.tolist(),
        index=guesses.cat_index,
    )
    num_col = st.selectbox(
        "Numeric column (aggregate)",
        options=df_raw.columns.tolist(),
        index=guesses.num_index,
    )

with st.sidebar.expander("2️⃣ Time Bucketing", expanded=True):
    period_grain = st.radio(
        "Bucket by:",
        options=["Quarter", "Month", "Year"],
        index=0,
        horizontal=True,
    )

with st.sidebar.expander("3️⃣ Concentration Buckets", expanded=True):
    percent_buckets_str = st.text_input(
        "Percent buckets (comma-separated)",
        value="10,20,50",
        help="Top X% of groups by count, e.g. 10,20,50",
    )
    ascending = st.checkbox(
        "Use ascending order (lowest first)?", value=False
    )

with st.sidebar.expander("4️⃣ Formatting", expanded=False):
    fmt_currency = st.text_input(
        "Number format (Python spec)",
        value=",.2f",
        help="E.g. ',.2f' → 1,234.56 ; ',.0f' → 1,235",
    )

# ------------------------------ PARSE SETTINGS ------------------------------ #
try:
    bucket_values: List[int] = sorted(
        {int(x.strip()) for x in percent_buckets_str.split(",") if x.strip() != ""}
    )
    bucket_values = [x for x in bucket_values if 0 < x <= 100]
    if not bucket_values:
        raise ValueError
except Exception:
    st.error("❌ Invalid bucket list. Example: 10,20,50")
    st.stop()

# ------------------------------ TYPE COERCION ------------------------------ #
try:
    df = df_raw.copy()
    df = coerce_dates_and_periods(df, time_col=time_col, period_grain=period_grain)
    df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
    df = df.dropna(subset=[time_col, "period", cat_col, num_col])
except Exception as e:
    st.error(f"❌ Column coercion failed: {e}")
    st.stop()

# ------------------------------ RUN ANALYSIS ------------------------------ #
st.subheader("📈 Concentration Results")

with st.spinner("Calculating..."):
    conc = concentration_by_period(
        df,
        period_col="period",
        group_col=cat_col,
        value_col=num_col,
        percent_buckets=bucket_values,
        ascending=ascending,
    )

if conc.empty:
    st.warning("⚠️ No results produced. Check your column selections.")
    st.stop()

conc_display = format_money_df(conc, fmt=fmt_currency)

st.dataframe(conc_display, use_container_width=True, height=500)

# ------------------------------ DOWNLOAD ------------------------------ #
st.markdown("### 💾 Export Results")
col1, col2 = st.columns(2)

csv_bytes = conc.to_csv(index=True).encode("utf-8")
with col1:
    st.download_button(
        "⬇️ Download CSV",
        data=csv_bytes,
        file_name=f"concentration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

xlsx_bytes = to_excel_bytes(conc)
with col2:
    st.download_button(
        "⬇️ Download Excel",
        data=xlsx_bytes,
        file_name=f"concentration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.caption(
    "Each cell shows the sum of the metric for the top X% of groups within that period. "
    "Row labels include the median group count across periods (like 'Top 10% (81)')."
)