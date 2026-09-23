"""
main.py
-------
End-to-end runnable version of the Supermarket Sales Analysis project.

Pipeline:
    1. Load the raw CSV dataset (data/supermarket_sales.csv)
    2. Clean the data (missing values, inconsistent text, dtypes)
    3. Recalculate Sales = Quantity x Unit Price
    4. Answer the six business questions from the project report
    5. Save summary charts to outputs/charts/
    6. Save a machine-readable summary to outputs/summary.json

Run:
    python src/main.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "supermarket_sales.csv"
CHARTS_DIR = ROOT / "outputs" / "charts"
SUMMARY_PATH = ROOT / "outputs" / "summary.json"

plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["axes.titleweight"] = "bold"


# ---------------------------------------------------------------------------
# 1-2-3. Load + clean + recalculate
# ---------------------------------------------------------------------------
def load_and_clean(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Normalize text columns (strip whitespace, fix casing)
    for col in ["Branch", "City", "Category", "Product", "CustomerType", "PaymentMethod"]:
        df[col] = df[col].astype(str).str.strip()
    df["Branch"] = df["Branch"].str.upper()
    df["CustomerType"] = df["CustomerType"].str.title()

    # Drop rows with a missing PaymentMethod / unusable text, since payment
    # method is central to one of the business questions
    df["PaymentMethod"] = df["PaymentMethod"].replace({"None": None, "nan": None})

    # Fill numeric gaps with column median (simple, standard imputation
    # for a small retail dataset) rather than dropping rows outright
    for col in ["Unit Price", "Quantity", "Rating"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    # Drop the handful of rows still missing a payment method
    df = df.dropna(subset=["PaymentMethod"]).reset_index(drop=True)

    # Recalculate Sales = Quantity x Unit Price (per the report's methodology)
    df["Sales"] = (df["Quantity"] * df["Unit Price"]).round(2)

    df["Date"] = pd.to_datetime(df["Date"])

    return df


# ---------------------------------------------------------------------------
# 4. Business questions
# ---------------------------------------------------------------------------
def analyze(df: pd.DataFrame) -> dict:
    results = {}

    # Q1: product with the highest sales
    by_product = df.groupby("Product")["Sales"].sum().sort_values(ascending=False)
    results["top_product"] = {"name": by_product.index[0], "sales": round(by_product.iloc[0], 2)}

    # Q2: best-performing branch
    by_branch = df.groupby(["Branch", "City"])["Sales"].sum().sort_values(ascending=False)
    top_branch_key = by_branch.index[0]
    results["top_branch"] = {
        "branch": top_branch_key[0],
        "city": top_branch_key[1],
        "sales": round(by_branch.iloc[0], 2),
    }

    # Q3: best-selling category
    by_category = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
    results["top_category"] = {"name": by_category.index[0], "sales": round(by_category.iloc[0], 2)}

    # Q4: most popular payment method
    by_payment = df["PaymentMethod"].value_counts()
    results["top_payment"] = {"method": by_payment.index[0], "count": int(by_payment.iloc[0])}

    # Q5: member vs normal average spend
    avg_by_customer = df.groupby("CustomerType")["Sales"].mean().round(2)
    member_avg = float(avg_by_customer.get("Member", float("nan")))
    normal_avg = float(avg_by_customer.get("Normal", float("nan")))
    results["member_vs_normal"] = {
        "member_avg": member_avg,
        "normal_avg": normal_avg,
        "members_spend_more": bool(member_avg > normal_avg),
    }

    # Q6: average rating
    results["avg_rating"] = round(float(df["Rating"].mean()), 2)

    # Extra context tables used by the report / notebook
    results["_tables"] = {
        "by_product": by_product.round(2).to_dict(),
        "by_branch": {f"{b} ({c})": round(v, 2) for (b, c), v in by_branch.items()},
        "by_category": by_category.round(2).to_dict(),
        "by_payment": by_payment.to_dict(),
    }
    return results


# ---------------------------------------------------------------------------
# 5. Charts
# ---------------------------------------------------------------------------
def make_charts(df: pd.DataFrame, results: dict, out_dir: Path = CHARTS_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Sales by product (top 10)
    by_product = df.groupby("Product")["Sales"].sum().sort_values(ascending=False).head(10)
    plt.figure(figsize=(8, 5))
    by_product.sort_values().plot(kind="barh", color="#2E86AB")
    plt.title("Top 10 Products by Sales")
    plt.xlabel("Sales (Rs.)")
    plt.tight_layout()
    plt.savefig(out_dir / "sales_by_product.png")
    plt.close()

    # Sales by branch
    by_branch = df.groupby("Branch")["Sales"].sum().sort_values(ascending=False)
    plt.figure(figsize=(6, 5))
    by_branch.plot(kind="bar", color="#A23B72")
    plt.title("Sales by Branch")
    plt.ylabel("Sales (Rs.)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_dir / "sales_by_branch.png")
    plt.close()

    # Sales by category
    by_category = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
    plt.figure(figsize=(7, 5))
    by_category.plot(kind="bar", color="#F18F01")
    plt.title("Sales by Category")
    plt.ylabel("Sales (Rs.)")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(out_dir / "sales_by_category.png")
    plt.close()

    # Payment method distribution
    by_payment = df["PaymentMethod"].value_counts()
    plt.figure(figsize=(5.5, 5.5))
    plt.pie(by_payment.values, labels=by_payment.index, autopct="%1.0f%%",
            colors=["#2E86AB", "#A23B72", "#F18F01"], startangle=90)
    plt.title("Payment Method Share")
    plt.tight_layout()
    plt.savefig(out_dir / "payment_method_share.png")
    plt.close()

    # Member vs Normal average spend
    avg_by_customer = df.groupby("CustomerType")["Sales"].mean().round(2)
    plt.figure(figsize=(5, 5))
    avg_by_customer.plot(kind="bar", color=["#2E86AB", "#A23B72"])
    plt.title("Average Spend: Member vs Normal")
    plt.ylabel("Average Sales (Rs.)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_dir / "member_vs_normal.png")
    plt.close()

    # Rating distribution
    plt.figure(figsize=(6, 5))
    df["Rating"].plot(kind="hist", bins=10, color="#3B8686", edgecolor="white")
    plt.axvline(results["avg_rating"], color="red", linestyle="--",
                label=f"Average = {results['avg_rating']}")
    plt.title("Customer Rating Distribution")
    plt.xlabel("Rating")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "rating_distribution.png")
    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    df = load_and_clean()
    results = analyze(df)
    make_charts(df, results)

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print("=== Supermarket Sales Analysis: Key Results ===")
    print(f"Rows analyzed (after cleaning): {len(df)}")
    print(f"1. Highest-selling product : {results['top_product']['name']} "
          f"(Rs. {results['top_product']['sales']:,})")
    print(f"2. Best-performing branch  : Branch {results['top_branch']['branch']} "
          f"({results['top_branch']['city']}) - Rs. {results['top_branch']['sales']:,}")
    print(f"3. Best-selling category   : {results['top_category']['name']} "
          f"(Rs. {results['top_category']['sales']:,})")
    print(f"4. Most popular payment    : {results['top_payment']['method']} "
          f"({results['top_payment']['count']} transactions)")
    m = results["member_vs_normal"]
    print(f"5. Member avg spend        : Rs. {m['member_avg']}")
    print(f"   Normal avg spend        : Rs. {m['normal_avg']}")
    print(f"   Members spend more?     : {m['members_spend_more']}")
    print(f"6. Average customer rating : {results['avg_rating']} / 5")
    print(f"\nCharts saved to: {CHARTS_DIR}")
    print(f"Summary JSON saved to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
