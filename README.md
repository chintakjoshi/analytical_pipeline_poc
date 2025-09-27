# Concentration Analysis POC

This project is a **lightweight proof-of-concept (POC)** for building an
analytical data pipeline that ingests Excel/CSV files, infers schema,
and computes a **concentration analysis**. It demonstrates how users can
upload financial data and generate insights like the **Top 10% / 20% /
50% contributions** per period, similar to the example output provided
in the spec.

------------------------------------------------------------------------

## Features

-   Upload CSV or Excel files with mixed categorical + numerical data
-   Schema inference (no hardcoding required)
-   Period bucketing (**Quarter / Month / Year**)
-   Concentration analysis:
    -   Dynamically aggregate into **Top 10%, 20%, 50%** of groups per
        period (by **count of groups**)
    -   Compute total values per period
-   Clean, human-readable output tables
-   Export results to **CSV** and **Excel**
-   Streamlit-based web UI for interaction
-   Modular core functions for reusability and extension

------------------------------------------------------------------------

## Project Structure

    your-project/
      app.py                  # Streamlit app
      requirements.txt        # Dependencies
      core/
        __init__.py
        data_ingest.py        # File loading, type coercion, column guessing
        concentration.py      # Concentration analysis logic
        utils.py              # Helpers for formatting & exporting

------------------------------------------------------------------------

## Setup

1.  Clone this repository:

    ``` bash
    git clone <your-repo-url>
    cd your-project
    ```

2.  (Optional) Create a virtual environment:

    ``` bash
    python -m venv venv
    source venv/bin/activate   # On Linux/Mac
    venv\Scripts\activate      # On Windows
    ```

3.  Install dependencies:

    ``` bash
    pip install -r requirements.txt
    ```

------------------------------------------------------------------------

## Running the App

Run the Streamlit application:

``` bash
streamlit run app.py
```

Open the provided URL in your browser (usually `http://localhost:8501`).

------------------------------------------------------------------------

## Usage

1.  **Upload a file**\
    Supported formats: `.csv`, `.xls`, `.xlsx`.

2.  **Select columns**

    -   Time column (date/timestamp)\
    -   Categorical column (e.g., customer/vendor ID)\
    -   Numeric column (e.g., revenue/amount)

3.  **Choose options**

    -   Period bucketing: Quarter / Month / Year\
    -   Percent buckets: default `10,20,50` (can be customized)\
    -   Order: Descending (top contributors) or Ascending (bottom
        contributors)

4.  **View output**

    -   Table shows Top 10% / 20% / 50% rows and a Total row\
    -   Each value is the sum of contributions for that slice\
    -   Row labels show median group counts across periods,
        e.g. `Top 10% (81)`

5.  **Export results**

    -   Download as `.csv`\
    -   Download as `.xlsx`

------------------------------------------------------------------------

## Design Notes

-   **Top X% is by group count**\
    For example, if there are 800 customers in a period, `Top 10%`
    selects the top 80 customers ranked by revenue.

-   **Schema inference**\
    Automatically guesses time, categorical, and numeric columns. User
    can override in UI.

-   **Scalability**\
    Core computation is vectorized with pandas. Can scale to millions of
    rows. For larger (10M+ rows), backend optimizations or Spark/Dask
    can be added later.

-   **Auditability**\
    Transformations are explicit, documented, and reproducible. Outputs
    can be re-run easily on new data.

------------------------------------------------------------------------

## Extending

-   Replace group-count concentration with **value-share concentration**
    (top X% of revenue instead of entities).
-   Add anomaly detection and schema change detection.
-   Integrate with databases (Postgres, Snowflake) instead of file
    upload.
-   Add Dockerfile for deployment.