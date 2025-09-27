import io
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
import streamlit as st

from core.data_ingest import load_any_table, coerce_dates_and_periods, guess_columns
from core.concentration import concentration_by_period
from core.utils import format_money_df, to_excel_bytes


# ------------------------------ UI HELPERS ------------------------------ #

st.set_page_config(page_title="Concentration Analysis POC", layout="wide")

st.title("Concentration Analysis (POC)")

with st.expander("Instructions", expanded=False):
    st.markdown(
        """
        1) Upload a CSV or Excel file with at least **one date/time**, **one categorical**, and **one numeric** column.  
        2) Select columns and aggregation options.  
        3) The app will compute **Top 10% / 20% / 50%** concentration **by count of groups** for each time period and show a wide table, plus provide a download.
        """
    )

# ------------------------------ FILE UPLOAD ------------------------------ #

uploaded = st.file_uploader("Upload data (.csv or .xlsx)", type=["csv", "xls", "xlsx"])

if uploaded is None:
    st.info("Waiting for a file…")
    st.stop()

# Read table (robust loader with type inference)
try:
    df_raw = load_any_table(uploaded)
except Exception as e:
    st.error(f"Could not read the file: {e}")
    st.stop()

if df_raw.empty:
    st.error("The file appears to have no rows.")
    st.stop()

st.success(f"Loaded {len(df_raw):,} rows × {df_raw.shape[1]} columns")

# ------------------------------ COLUMN GUESSING ------------------------------ #

guesses = guess_columns(df_raw)

col1, col2, col3 = st.columns(3)
with col1:
    time_col = st.selectbox(
        "Time column",
        options=df_raw.columns.tolist(),
        index=guesses.time_index,
        help="Column interpreted as timestamp or date",
    )
with col2:
    cat_col = st.selectbox(
        "Categorical (group-by) column",
        options=df_raw.columns.tolist(),
        index=guesses.cat_index,
        help="Entity you want the concentration across (e.g., Customer, Vendor)",
    )
with col3:
    num_col = st.selectbox(
        "Numeric (amount/metric) column",
        options=df_raw.columns.tolist(),
        index=guesses.num_index,
        help="Value to aggregate within each period",
    )

period_grain = st.radio(
    "Time bucketing",
    options=["Quarter", "Month", "Year"],
    index=0,
    horizontal=True,
)

percent_buckets_str = st.text_input(
    "Percent buckets (comma-separated, 0–100)",
    value="10,20,50",
    help="Defines the 'Top X%' rows; percentages are by **count of groups per period**.",
)

ascending = st.checkbox(
    "Use ascending order (lowest values first)?",
    value=False,
    help="Normally you want the top contributors (descending). Toggle if you need the smallest.",
)

fmt_currency = st.text_input(
    "Number format (Python format spec)",
    value=",.2f",
    help="Applied to all numeric cells, e.g., ',.2f' for 1,234.56 or ',.0f' for integers.",
)

# Parse buckets
try:
    bucket_values: List[int] = sorted(
        {int(x.strip()) for x in percent_buckets_str.split(",") if x.strip() != ""}
    )
    bucket_values = [x for x in bucket_values if 0 < x <= 100]
    if not bucket_values:
        raise ValueError
except Exception:
    st.error("Please provide valid percentages like: 10,20,50")
    st.stop()

# ------------------------------ TYPE COERCION ------------------------------ #

try:
    df = df_raw.copy()
    df = coerce_dates_and_periods(df, time_col=time_col, period_grain=period_grain)
    # Coerce numeric
    df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
    df = df.dropna(subset=[time_col, "period", cat_col, num_col])
except Exception as e:
    st.error(f"Type coercion failed: {e}")
    st.stop()

# ------------------------------ COMPUTE ------------------------------ #

with st.spinner("Computing concentration table…"):
    conc = concentration_by_period(
        df,
        period_col="period",
        group_col=cat_col,
        value_col=num_col,
        percent_buckets=bucket_values,
        ascending=ascending,
    )

# Optional currency-like formatting to resemble your screenshot
conc_display = format_money_df(conc, fmt=fmt_currency)

st.subheader("Concentration table")
st.caption(
    "Each cell is the sum of the selected metric contributed by the top X% of groups (by count) within that period. "
    "The number in parentheses is the number of groups included for that period."
)
st.dataframe(conc_display, use_container_width=True)


# ------------------------------ DOWNLOADS ------------------------------ #

csv_bytes = conc.to_csv(index=True).encode("utf-8")
st.download_button(
    "Download CSV",
    data=csv_bytes,
    file_name=f"concentration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
)

xlsx_bytes = to_excel_bytes(conc)
st.download_button(
    "Download Excel",
    data=xlsx_bytes,
    file_name=f"concentration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
