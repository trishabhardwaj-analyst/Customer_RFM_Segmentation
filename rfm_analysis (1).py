import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


# ============================================================
# CUSTOMER RFM SEGMENTATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

FILE_PATH = DATA_DIR / "online_retail_II.xlsx"


def find_column(df, candidates):
    """Return the first matching column from a list of aliases."""
    normalized = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in normalized:
            return normalized[key]
    return None


def main():
    print("=" * 60)
    print("CUSTOMER RFM SEGMENTATION")
    print("=" * 60)

    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {FILE_PATH}\n"
            "Place Online Retail II Excel file in the data folder "
            "and name it online_retail_II.xlsx."
        )

    # --------------------------------------------------------
    # 1. LOAD ALL SHEETS
    # --------------------------------------------------------
    excel = pd.ExcelFile(FILE_PATH)
    print("\nWorkbook sheets:", excel.sheet_names)

    frames = []
    for sheet in excel.sheet_names:
        temp = pd.read_excel(FILE_PATH, sheet_name=sheet)
        temp.columns = temp.columns.astype(str).str.strip()
        frames.append(temp)

    df = pd.concat(frames, ignore_index=True)

    print("Raw rows:", len(df))
    print("Columns:", list(df.columns))

    # --------------------------------------------------------
    # 2. IDENTIFY COLUMN NAMES
    # --------------------------------------------------------
    invoice_col = find_column(df, ["Invoice", "InvoiceNo", "Invoice No"])
    stock_col = find_column(df, ["StockCode", "Stock Code"])
    description_col = find_column(df, ["Description"])
    quantity_col = find_column(df, ["Quantity"])
    date_col = find_column(df, ["InvoiceDate", "Invoice Date"])
    price_col = find_column(df, ["Price", "UnitPrice", "Unit Price"])
    customer_col = find_column(
        df, ["Customer ID", "CustomerID", "Customer Id"]
    )
    country_col = find_column(df, ["Country"])

    required = {
        "Invoice": invoice_col,
        "Quantity": quantity_col,
        "InvoiceDate": date_col,
        "Price": price_col,
        "CustomerID": customer_col,
    }

    missing = [name for name, col in required.items() if col is None]
    if missing:
        raise ValueError(
            "Could not identify required columns: "
            + ", ".join(missing)
            + "\nAvailable columns: "
            + ", ".join(map(str, df.columns))
        )

    # --------------------------------------------------------
    # 3. STANDARDIZE WORKING COLUMNS
    # --------------------------------------------------------
    rename_map = {
        invoice_col: "Invoice",
        quantity_col: "Quantity",
        date_col: "InvoiceDate",
        price_col: "UnitPrice",
        customer_col: "CustomerID",
    }

    df = df.rename(columns=rename_map)

    # --------------------------------------------------------
    # 4. DATA CLEANING
    # --------------------------------------------------------
    before = len(df)

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"], errors="coerce"
    )
    df["Quantity"] = pd.to_numeric(
        df["Quantity"], errors="coerce"
    )
    df["UnitPrice"] = pd.to_numeric(
        df["UnitPrice"], errors="coerce"
    )

    df = df.dropna(
        subset=[
            "Invoice",
            "InvoiceDate",
            "Quantity",
            "UnitPrice",
            "CustomerID",
        ]
    )

    # Remove cancelled invoices.
    df = df[
        ~df["Invoice"].astype(str).str.upper().str.startswith("C")
    ]

    # Keep valid purchases only.
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    print(f"Rows removed during cleaning: {before - len(df)}")
    print(f"Clean transaction rows: {len(df):,}")

    # --------------------------------------------------------
    # 5. REVENUE
    # --------------------------------------------------------
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    # --------------------------------------------------------
    # 6. ANALYSIS DATE
    # --------------------------------------------------------
    analysis_date = (
        df["InvoiceDate"].max() + pd.Timedelta(days=1)
    )

    print("Analysis date:", analysis_date.date())

    # --------------------------------------------------------
    # 7. RFM METRICS
    # --------------------------------------------------------
    rfm = (
        df.groupby("CustomerID")
        .agg(
            Recency=(
                "InvoiceDate",
                lambda x: (analysis_date - x.max()).days
            ),
            Frequency=("Invoice", "nunique"),
            Monetary=("Revenue", "sum"),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # 8. RFM SCORES
    # --------------------------------------------------------
    # Recency: lower is better, so labels are reversed.
    rfm["R_Score"] = pd.qcut(
        rfm["Recency"],
        q=5,
        labels=[5, 4, 3, 2, 1],
        duplicates="drop",
    ).astype(int)

    # Ranking avoids qcut problems caused by many tied
    # Frequency values.
    frequency_rank = rfm["Frequency"].rank(
        method="first"
    )

    rfm["F_Score"] = pd.qcut(
        frequency_rank,
        q=5,
        labels=[1, 2, 3, 4, 5],
        duplicates="drop",
    ).astype(int)

    # Monetary: higher is better.
    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"],
        q=5,
        labels=[1, 2, 3, 4, 5],
        duplicates="drop",
    ).astype(int)

    rfm["RFM_Score"] = (
        rfm["R_Score"]
        + rfm["F_Score"]
        + rfm["M_Score"]
    )

    # --------------------------------------------------------
    # 9. CUSTOMER SEGMENTS
    # --------------------------------------------------------
    def segment_customer(row):
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 4 and f >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "Recent Customers"
        elif r <= 2 and f >= 4 and m >= 3:
            return "At Risk"
        elif r <= 2 and f <= 2 and m <= 2:
            return "Lost Customers"
        elif m >= 4:
            return "High Value"
        else:
            return "Potential Loyalists"

    rfm["Segment"] = rfm.apply(
        segment_customer, axis=1
    )

    # --------------------------------------------------------
    # 10. FINAL RFM TABLE
    # --------------------------------------------------------
    rfm = rfm.sort_values(
        ["RFM_Score", "Monetary"],
        ascending=[False, False]
    )

    rfm.to_csv(
        DATA_DIR / "rfm_customer_table.csv",
        index=False
    )

    # --------------------------------------------------------
    # 11. SEGMENT SUMMARY
    # --------------------------------------------------------
    segment_summary = (
        rfm.groupby("Segment")
        .agg(
            Customers=("CustomerID", "count"),
            Average_Recency=("Recency", "mean"),
            Average_Frequency=("Frequency", "mean"),
            Average_Monetary=("Monetary", "mean"),
            Total_Revenue=("Monetary", "sum"),
        )
        .reset_index()
    )

    segment_summary["Customer_Percentage"] = (
        segment_summary["Customers"]
        / segment_summary["Customers"].sum()
        * 100
    )

    segment_summary["Revenue_Percentage"] = (
        segment_summary["Total_Revenue"]
        / segment_summary["Total_Revenue"].sum()
        * 100
    )

    segment_summary = segment_summary.round(2)
    segment_summary = segment_summary.sort_values(
        "Total_Revenue",
        ascending=False
    )

    segment_summary.to_csv(
        DATA_DIR / "segment_summary.csv",
        index=False
    )

    # --------------------------------------------------------
    # 12. PRINT RESULTS
    # --------------------------------------------------------
    print("\nRFM TABLE SAMPLE:")
    print(rfm.head(10).to_string(index=False))

    print("\nSEGMENT SUMMARY:")
    print(segment_summary.to_string(index=False))

    # --------------------------------------------------------
    # 13. CHART 1: CUSTOMER COUNT
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=segment_summary,
        x="Segment",
        y="Customers",
    )
    plt.xticks(rotation=35, ha="right")
    plt.title("Customer Count by RFM Segment")
    plt.xlabel("Customer Segment")
    plt.ylabel("Number of Customers")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "segment_distribution.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    # --------------------------------------------------------
    # 14. CHART 2: REVENUE BY SEGMENT
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=segment_summary,
        x="Segment",
        y="Total_Revenue",
    )
    plt.xticks(rotation=35, ha="right")
    plt.title("Revenue by RFM Segment")
    plt.xlabel("Customer Segment")
    plt.ylabel("Total Revenue")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "revenue_by_segment.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    # --------------------------------------------------------
    # 15. CHART 3: RFM SCORE DISTRIBUTION
    # --------------------------------------------------------
    plt.figure(figsize=(10, 6))
    sns.histplot(
        data=rfm,
        x="RFM_Score",
        discrete=True,
    )
    plt.title("Distribution of Customer RFM Scores")
    plt.xlabel("RFM Score")
    plt.ylabel("Number of Customers")
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "rfm_distribution.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()

    print("\nAnalysis completed successfully.")
    print("Created:")
    print(" - data/rfm_customer_table.csv")
    print(" - data/segment_summary.csv")
    print(" - outputs/segment_distribution.png")
    print(" - outputs/revenue_by_segment.png")
    print(" - outputs/rfm_distribution.png")


if __name__ == "__main__":
    main()
