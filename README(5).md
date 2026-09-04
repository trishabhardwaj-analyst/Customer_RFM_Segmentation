# Customer RFM Segmentation

## Project Overview
Customer RFM Segmentation is a data analytics project based on the **Online Retail II** dataset.

RFM stands for:
- **Recency** – how recently a customer purchased
- **Frequency** – how often a customer purchased
- **Monetary** – how much a customer spent

The project cleans transaction data, calculates customer-level RFM metrics, assigns 1–5 scores, creates practical customer segments, summarizes segment performance, and produces business recommendations.

## Tools
- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- SQL / MySQL

## Project Structure
```text
Customer_RFM_Segmentation/
├── README.md
├── requirements.txt
├── rfm_analysis.py
├── .gitignore
├── LICENSE
├── data/
│   ├── online_retail_II.xlsx
│   ├── rfm_customer_table.csv
│   └── segment_summary.csv
├── sql/
│   └── rfm_analysis.sql
├── reports/
│   └── RFM_Segmentation_Report.md
└── outputs/
    ├── segment_distribution.png
    ├── revenue_by_segment.png
    └── rfm_distribution.png
```

## Dataset
Use the **Online Retail II** dataset and place the Excel file here:

`data/online_retail_II.xlsx`

The Python script automatically combines all sheets in the workbook.

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Place the dataset
Put `online_retail_II.xlsx` inside the `data` folder.

### 3. Run the analysis
```bash
python rfm_analysis.py
```

### 4. Generated files
The script creates:
- `data/rfm_customer_table.csv`
- `data/segment_summary.csv`
- `outputs/segment_distribution.png`
- `outputs/revenue_by_segment.png`
- `outputs/rfm_distribution.png`

## RFM Scoring
Each customer receives a score from 1 to 5 for each dimension.

- Recency: lower number of days is better
- Frequency: higher number of purchases is better
- Monetary: higher spending is better

The total RFM score ranges from 3 to 15.

## Customer Segments
The project uses the following practical segments:
- Champions
- Loyal Customers
- Recent Customers
- At Risk
- Lost Customers
- High Value
- Potential Loyalists

## Business Use
The segmentation can support:
- Customer retention
- Win-back campaigns
- Loyalty programs
- Cross-selling
- Personalized marketing
- Customer prioritization

## Important Note
The exact customer counts, revenue values, and segment sizes are generated from the dataset when the script is run. Do not manually invent these values in the final report.
