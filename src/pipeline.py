
import pandas as pd
from pathlib import Path

RAW_FILE = Path(__file__).resolve().parents[1] / "data" / "raw" / "transactions.csv"
CURATED_DIR = Path(__file__).resolve().parents[1] / "data" / "curated"
CURATED_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = CURATED_DIR / "sales_summary.csv"

# Load data
df = pd.read_csv(RAW_FILE, parse_dates=["order_date"])

# Clean data
df.dropna(inplace=True)
df["revenue"] = df["quantity"] * df["unit_price"]

# Aggregate by month and category
summary = df.groupby([df["order_date"].dt.to_period("M"), "category"]).agg(
    total_orders=("order_id", "count"),
    total_revenue=("revenue", "sum"),
    avg_order_value=("revenue", "mean")
).reset_index()

summary.rename(columns={"order_date": "month"}, inplace=True)

# Save curated data
summary.to_csv(OUT_FILE, index=False)
print(f"Saved summary to {OUT_FILE}")
