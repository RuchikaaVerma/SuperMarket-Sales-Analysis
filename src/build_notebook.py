"""
build_notebook.py
------------------
Programmatically assembles notebooks/Supermarket_Sales_Analysis.ipynb
from the same logic used in src/main.py, so the notebook and the script
never drift apart. Run this, then execute the notebook with nbconvert.
"""

import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_PATH = ROOT / "notebooks" / "Supermarket_Sales_Analysis.ipynb"

nb = nbf.v4.new_notebook()
cells = []

md = lambda src: cells.append(nbf.v4.new_markdown_cell(src))
code = lambda src: cells.append(nbf.v4.new_code_cell(src))

md("""\
# Supermarket Sales Analysis - Data Analytics Project

**Goal:** Analyze supermarket sales data and find useful information about products, branches,
categories, customers, payment methods, and ratings.

**Dataset:** 500 simulated sales transactions (`data/supermarket_sales.csv`) with product, branch,
city, customer type, quantity, unit price, payment method, and rating.

**Notebook sections**
1. Load libraries and data
2. Data cleaning
3. Feature engineering (Sales = Quantity x Unit Price)
4. Business question analysis (with charts)
5. Business decisions & conclusion
""")

code("""\
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 100
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["axes.titleweight"] = "bold"

DATA_PATH = "../data/supermarket_sales.csv"
df_raw = pd.read_csv(DATA_PATH)
print(f"Rows: {len(df_raw)}, Columns: {list(df_raw.columns)}")
df_raw.head()
""")

md("## 2. Data Cleaning\n\nCheck for missing values and inconsistent text before doing any analysis.")

code("""\
df_raw.isna().sum()
""")

code("""\
df = df_raw.copy()

# Normalize text columns (strip whitespace, fix casing)
for col in ["Branch", "City", "Category", "Product", "CustomerType", "PaymentMethod"]:
    df[col] = df[col].astype(str).str.strip()
df["Branch"] = df["Branch"].str.upper()
df["CustomerType"] = df["CustomerType"].str.title()
df["PaymentMethod"] = df["PaymentMethod"].replace({"None": None, "nan": None})

# Fill numeric gaps with the column median
for col in ["Unit Price", "Quantity", "Rating"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df[col] = df[col].fillna(df[col].median())

# Drop rows still missing a payment method (needed for Q4)
df = df.dropna(subset=["PaymentMethod"]).reset_index(drop=True)
df["Date"] = pd.to_datetime(df["Date"])

print(f"Rows after cleaning: {len(df)}")
df.isna().sum()
""")

md("## 3. Feature Engineering\n\nRecalculate `Sales = Quantity x Unit Price` for every row, per the project methodology.")

code("""\
df["Sales"] = (df["Quantity"] * df["Unit Price"]).round(2)
df[["Product", "Branch", "Quantity", "Unit Price", "Sales"]].head()
""")

md("## 4. Business Questions\n\n### Q1. Which product generates the highest sales?")

code("""\
by_product = df.groupby("Product")["Sales"].sum().sort_values(ascending=False)
top_product, top_product_sales = by_product.index[0], by_product.iloc[0]
print(f"Top product: {top_product} -> Rs. {top_product_sales:,.2f}")

by_product.head(10).sort_values().plot(kind="barh", color="#2E86AB", figsize=(8, 5))
plt.title("Top 10 Products by Sales")
plt.xlabel("Sales (Rs.)")
plt.tight_layout()
plt.show()
""")

md("### Q2. Which branch performs best?")

code("""\
by_branch = df.groupby(["Branch", "City"])["Sales"].sum().sort_values(ascending=False)
print(by_branch)

df.groupby("Branch")["Sales"].sum().sort_values(ascending=False).plot(
    kind="bar", color="#A23B72", figsize=(6, 5))
plt.title("Sales by Branch")
plt.ylabel("Sales (Rs.)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()
""")

md("### Q3. Which category sells the most?")

code("""\
by_category = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
print(by_category)

by_category.plot(kind="bar", color="#F18F01", figsize=(7, 5))
plt.title("Sales by Category")
plt.ylabel("Sales (Rs.)")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.show()
""")

md("### Q4. What is the most popular payment method?")

code("""\
by_payment = df["PaymentMethod"].value_counts()
print(by_payment)

plt.figure(figsize=(5.5, 5.5))
plt.pie(by_payment.values, labels=by_payment.index, autopct="%1.0f%%",
        colors=["#2E86AB", "#A23B72", "#F18F01"], startangle=90)
plt.title("Payment Method Share")
plt.tight_layout()
plt.show()
""")

md("### Q5. Do Members spend more than Normal customers?")

code("""\
avg_by_customer = df.groupby("CustomerType")["Sales"].mean().round(2)
print(avg_by_customer)

avg_by_customer.plot(kind="bar", color=["#2E86AB", "#A23B72"], figsize=(5, 5))
plt.title("Average Spend: Member vs Normal")
plt.ylabel("Average Sales (Rs.)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()
""")

md("### Q6. What is the average customer rating?")

code("""\
avg_rating = round(df["Rating"].mean(), 2)
print(f"Average rating: {avg_rating} / 5")

df["Rating"].plot(kind="hist", bins=10, color="#3B8686", edgecolor="white", figsize=(6, 5))
plt.axvline(avg_rating, color="red", linestyle="--", label=f"Average = {avg_rating}")
plt.title("Customer Rating Distribution")
plt.xlabel("Rating")
plt.legend()
plt.tight_layout()
plt.show()
""")

md("""\
## 5. Business Decisions

- Keep more stock of high-selling products (e.g. the top product identified above) and categories.
- Study the reasons for the best-performing branch's strong performance and try to replicate them elsewhere.
- Continue supporting and promoting the most popular payment method.
- Improve customer service in areas where ratings are lower, to lift the overall average rating.
- Use the member vs normal spending comparison to redesign membership offers so they actually pay off.

## 6. Conclusion

This notebook shows, end to end, how raw transaction-level sales data can be cleaned and converted
into simple, decision-ready insights: top products, best branches, leading categories, preferred
payment methods, customer-segment spending patterns, and satisfaction levels.
""")

nb["cells"] = cells
NB_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(NB_PATH, "w") as f:
    nbf.write(nb, f)

print(f"Notebook written to {NB_PATH}")
