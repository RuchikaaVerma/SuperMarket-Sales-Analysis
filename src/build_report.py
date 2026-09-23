"""
build_report.py
----------------
Builds report/Supermarket_Sales_Analysis_Report.pdf using the real,
computed results from outputs/summary.json and the charts in
outputs/charts/. Mirrors the structure of the original project brief but
fills every number in with the actual output of the analysis pipeline.

Run (after src/main.py has produced outputs/summary.json and charts):
    python src/build_report.py
"""

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem,
    Table, TableStyle, PageBreak
)

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "outputs" / "charts"
SUMMARY = ROOT / "outputs" / "summary.json"
OUT_PDF = ROOT / "report" / "Supermarket_Sales_Analysis_Report.pdf"

with open(SUMMARY) as f:
    R = json.load(f)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1c", parent=styles["Heading1"], spaceAfter=10, textColor=colors.HexColor("#1B3B5F")))
styles.add(ParagraphStyle("H2c", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#2E86AB")))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=15))
styles.add(ParagraphStyle("Answer", parent=styles["Normal"], fontSize=10.5, leading=15,
                           leftIndent=10, textColor=colors.HexColor("#1B3B5F")))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=8.5, leading=11,
                           textColor=colors.grey, alignment=1))

story = []

# ---------------------------------------------------------------- Title ---
story.append(Paragraph("Supermarket Sales Analysis", styles["Title"]))
story.append(Paragraph("Data Analytics Project", styles["Heading3"]))
story.append(Spacer(1, 12))

# ---------------------------------------------------------- 1. Problem ---
story.append(Paragraph("1. Problem Statement", styles["H1c"]))
story.append(Paragraph(
    "The aim of this project is to analyze supermarket sales data and find useful information "
    "about products, branches, categories, customers, payments, and ratings.",
    styles["Body"]))

# ------------------------------------------------------------- 2. Data ---
story.append(Paragraph("2. Dataset", styles["H1c"]))
story.append(Paragraph(
    "The dataset contains 500 sales transactions across three branches (Kanpur, Delhi, and Mumbai). "
    "It includes product, category, branch, city, customer type, quantity, unit price, payment method, "
    "and customer rating for each transaction. Six rows contained intentionally messy values "
    "(missing prices, quantities, ratings, or a missing payment method, plus inconsistent text "
    "casing) to make the cleaning step meaningful; these were cleaned during analysis.",
    styles["Body"]))

# --------------------------------------------------------------- 3. Steps ---
story.append(Paragraph("3. Steps Used for Analysis", styles["H1c"]))
steps = [
    "Collect and load the CSV dataset (data/supermarket_sales.csv).",
    "Check the data for missing or incorrect values and clean it (strip whitespace, fix "
    "inconsistent casing, impute missing numeric values with the column median, drop rows "
    "with no payment method).",
    "Calculate Sales = Quantity x Unit Price.",
    "Group and summarize the data using totals, counts, and averages.",
    "Create charts to compare the results.",
    "Use the results to make business decisions.",
]
story.append(ListFlowable(
    [ListItem(Paragraph(s, styles["Body"])) for s in steps],
    bulletType="1", leftIndent=18))

# ------------------------------------------------------------ 4. Live -----
story.append(Paragraph("4. Live Analysis", styles["H1c"]))


def qa(question, answer, image_name=None, caption=None):
    story.append(Paragraph(question, styles["Heading4"]))
    story.append(Paragraph(answer, styles["Answer"]))
    if image_name:
        story.append(Spacer(1, 6))
        story.append(Image(str(CHARTS / image_name), width=13 * cm, height=13 * cm * 0.72))
        if caption:
            story.append(Paragraph(caption, styles["Caption"]))
    story.append(Spacer(1, 10))


qa(
    "Which product generates the highest sales?",
    f"<b>{R['top_product']['name']}</b> generated the highest sales: "
    f"Rs. {R['top_product']['sales']:,.2f}.",
    "sales_by_product.png", "Figure 1: Top 10 products by total sales."
)

qa(
    "Which branch performs best?",
    f"<b>Branch {R['top_branch']['branch']} ({R['top_branch']['city']})</b> performed best "
    f"with sales of Rs. {R['top_branch']['sales']:,.2f}.",
    "sales_by_branch.png", "Figure 2: Total sales by branch."
)

qa(
    "Which category sells the most?",
    f"<b>{R['top_category']['name']}</b> had the highest sales with "
    f"Rs. {R['top_category']['sales']:,.2f}.",
    "sales_by_category.png", "Figure 3: Total sales by product category."
)

qa(
    "What is the most popular payment method?",
    f"<b>{R['top_payment']['method']}</b> was the most used payment method with "
    f"{R['top_payment']['count']} transactions.",
    "payment_method_share.png", "Figure 4: Share of transactions by payment method."
)

m = R["member_vs_normal"]
verdict = "Yes" if m["members_spend_more"] else "No"
qa(
    "Do Members spend more than Normal customers?",
    f"<b>{verdict}.</b> The average Member transaction was Rs. {m['member_avg']:.2f}, "
    f"while Normal customers averaged Rs. {m['normal_avg']:.2f}.",
    "member_vs_normal.png", "Figure 5: Average sale amount by customer type."
)

qa(
    "What is the average customer rating?",
    f"The average customer rating was <b>{R['avg_rating']} out of 5</b>.",
    "rating_distribution.png", "Figure 6: Distribution of customer ratings."
)

story.append(PageBreak())

# ---------------------------------------------------------- Summary table ---
story.append(Paragraph("Summary Table: Sales by Category", styles["H1c"]))
cat_rows = [["Category", "Total Sales (Rs.)"]]
for cat, val in R["_tables"]["by_category"].items():
    cat_rows.append([cat, f"{val:,.2f}"])
t = Table(cat_rows, colWidths=[8 * cm, 5 * cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3B5F")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF3F6")]),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t)
story.append(Spacer(1, 16))

# --------------------------------------------------------- 5. Decisions ---
story.append(Paragraph("5. Business Decisions", styles["H1c"]))
decisions = [
    "Keep more stock of high-selling products and categories such as the top product and "
    "category identified above.",
    "Study the reasons for the best-performing branch's strong performance and apply the "
    "same practices at the other branches.",
    "Continue supporting and promoting the most-used payment method to keep checkout friction low.",
    "Improve customer service to increase ratings where they are lower than average.",
    "Use the member vs. normal spending comparison to redesign membership offers so they "
    "genuinely increase spend.",
]
story.append(ListFlowable(
    [ListItem(Paragraph(d, styles["Body"])) for d in decisions],
    bulletType="bullet", leftIndent=18))

# ------------------------------------------------------------ 6. Conclu ---
story.append(Paragraph("6. Conclusion", styles["H1c"]))
story.append(Paragraph(
    "This analysis shows how sales data can be converted into simple insights that help a "
    "supermarket understand performance and make better decisions. The full, runnable pipeline "
    "used to produce every figure and chart in this report is included alongside it "
    "(see README.md for run instructions).",
    styles["Body"]))

story.append(Spacer(1, 20))
story.append(Paragraph(
    "Note: This project uses a simulated 500-row dataset built to reflect the same patterns "
    "described in the original project brief (top product, best branch, leading category, "
    "preferred payment method, membership spending comparison, and average rating). All figures "
    "above are computed directly from that dataset by the code in this project, not hand-typed.",
    styles["Caption"]))

OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT_PDF), pagesize=A4,
                         topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                         leftMargin=1.8 * cm, rightMargin=1.8 * cm)
doc.build(story)
print(f"Report written to {OUT_PDF}")
