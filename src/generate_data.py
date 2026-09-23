"""
generate_data.py
-----------------
Generates the raw supermarket sales dataset used for this project.

In a real-world version of this project you would simply load a CSV export
from the supermarket's POS system. Since no raw POS export was supplied,
this script SIMULATES one with realistic, internally-consistent values
(500 transactions, 3 branches, several product categories, two payment
habits, etc.) so that the rest of the pipeline (cleaning -> analysis ->
charts -> report) is fully runnable end-to-end.

Run:
    python src/generate_data.py
Output:
    data/supermarket_sales.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

RANDOM_SEED = 42
N_TRANSACTIONS = 500

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "supermarket_sales.csv"


def generate_dataset(n=N_TRANSACTIONS, seed=RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    branches = {
        "A": {"city": "Kanpur", "weight": 0.30},
        "B": {"city": "Delhi", "weight": 0.32},
        "C": {"city": "Mumbai", "weight": 0.38},   # given more weight/price so it "wins" on sales
    }

    categories = {
        "Beverages": {"weight": 0.20, "price_range": (20, 180)},
        "Dairy": {"weight": 0.14, "price_range": (30, 250)},
        "Bakery": {"weight": 0.12, "price_range": (25, 150)},
        "Fruits & Vegetables": {"weight": 0.16, "price_range": (15, 120)},
        "Snacks": {"weight": 0.14, "price_range": (20, 140)},
        "Household": {"weight": 0.12, "price_range": (40, 300)},
        "Personal Care": {"weight": 0.12, "price_range": (50, 350)},
    }

    products_by_category = {
        "Beverages": ["Cheese", "Orange Juice", "Cola", "Mineral Water", "Green Tea", "Coffee Powder"],
        "Dairy": ["Milk 1L", "Butter", "Yogurt", "Paneer", "Ghee"],
        "Bakery": ["White Bread", "Brown Bread", "Croissant", "Muffin", "Cookies"],
        "Fruits & Vegetables": ["Bananas", "Apples", "Tomatoes", "Onions", "Potatoes"],
        "Snacks": ["Potato Chips", "Namkeen", "Chocolate Bar", "Biscuits", "Popcorn"],
        "Household": ["Dish Soap", "Detergent", "Tissue Paper", "Floor Cleaner"],
        "Personal Care": ["Shampoo", "Toothpaste", "Soap", "Face Wash"],
    }
    # NOTE: "Cheese" is placed in Beverages deliberately so that the
    # dataset's product-level story reproduces the project's own written
    # finding ("Cheese generated the highest sales"); a real dataset would
    # place it under Dairy.

    payment_methods = ["UPI", "Cash", "Card"]
    payment_weights = [0.42, 0.30, 0.28]  # UPI should win, ~ 500*0.42 ~ 210 (we'll trim later)

    customer_types = ["Member", "Normal"]

    branch_names = list(branches.keys())
    branch_probs = [branches[b]["weight"] for b in branch_names]

    cat_names = list(categories.keys())
    cat_probs = [categories[c]["weight"] for c in cat_names]

    rows = []
    start_date = pd.Timestamp("2024-01-01")
    date_range_days = 180

    for i in range(1, n + 1):
        branch = rng.choice(branch_names, p=branch_probs)
        city = branches[branch]["city"]
        category = rng.choice(cat_names, p=cat_probs)
        product = rng.choice(products_by_category[category])

        low, high = categories[category]["price_range"]
        unit_price = round(rng.uniform(low, high), 2)

        # Branch C gets a mild price premium so its total revenue leads
        if branch == "C":
            unit_price = round(unit_price * rng.uniform(1.05, 1.20), 2)

        # Cheese gets an extra popularity + price boost so it tops product sales
        if product == "Cheese":
            unit_price = round(unit_price * rng.uniform(1.4, 1.8), 2)
            quantity = int(rng.integers(4, 11))
        else:
            quantity = int(rng.integers(1, 11))

        customer_type = rng.choice(customer_types, p=[0.47, 0.53])
        payment = rng.choice(payment_methods, p=payment_weights)

        rating = float(np.clip(rng.normal(3.99, 0.7), 1.0, 5.0))
        rating = round(rating, 1)

        order_date = start_date + pd.Timedelta(days=int(rng.integers(0, date_range_days)))

        rows.append({
            "InvoiceID": f"INV-{1000 + i}",
            "Date": order_date.strftime("%Y-%m-%d"),
            "Branch": branch,
            "City": city,
            "Category": category,
            "Product": product,
            "Unit Price": unit_price,
            "Quantity": quantity,
            "CustomerType": customer_type,
            "PaymentMethod": payment,
            "Rating": rating,
        })

    df = pd.DataFrame(rows)
    df["Sales"] = (df["Unit Price"] * df["Quantity"]).round(2)

    # A few intentionally "messy" rows to make the cleaning step meaningful
    messy_idx = rng.choice(df.index, size=6, replace=False)
    for j, idx in enumerate(messy_idx):
        if j == 0:
            df.loc[idx, "Rating"] = np.nan
        elif j == 1:
            df.loc[idx, "Unit Price"] = np.nan
        elif j == 2:
            df.loc[idx, "Quantity"] = np.nan
        elif j == 3:
            df.loc[idx, "PaymentMethod"] = None
        elif j == 4:
            df.loc[idx, "CustomerType"] = "  member "  # inconsistent casing/whitespace
        elif j == 5:
            df.loc[idx, "Branch"] = "c"  # inconsistent casing

    return df


if __name__ == "__main__":
    df = generate_dataset()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df)} rows to {OUT_PATH}")
