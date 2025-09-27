import pandas as pd
from app.analysis import concentration

def test_concentration_basic():
    df = pd.DataFrame({
        "period": ["2024","2024","2024","2024"],
        "group": ["A","B","C","D"],
        "value": [50, 30, 15, 5],
    })
    by_gp, summary = concentration(df, "group", "value", "period")
    assert "Top 10%" in by_gp["bucket"].unique()
    assert summary.groupby("period")["total_metric"].sum().iloc[0] == 100