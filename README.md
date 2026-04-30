# Final Project Milestone

**Team 19**: Ian Donnen, Audrey Doyle, Rylee Lindermuth

## Overview
This repository contains an automated, parameterizable Python data pipeline developed to
analyze the Olist Brazilian e-commerce dataset. Managed via uv, the system performs pre-flight
data validation, executes parameterized DuckDB SQL queries, and uses Polars to process dynamic
command-line filters. The pipeline generates scalable business intelligence, outputting summary
CSVs, machine-readable Parquet files, interactive Altair visualizations, and a formatted Excel
report delivered as a self-contained stakeholder deliverable.

## How to Run

Instructions to run the pipeline from a fresh clone:

```bash
git clone https://github.com/imd00008/wvu-ieng-331-final-19.git
cd wvu-ieng-331-final-19
uv sync
# place olist.duckdb in the data/ directory
uv run wvu-ieng-331-final-19
uv run wvu-ieng-331-final-19 --start-date 2017-01-01 --seller-state SP
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--start-date` | string | None (no filter) | Filters orders to only include those purchased on or after the provided date (Format: YYYY-MM-DD). |
| `--seller-state` | string | None (no filter) | Filters the analysis to a specific Brazilian state using its 2-letter abbreviation (e.g., SP, RJ, MG). |

## Outputs

All generated reports are stored in the `output/` directory:

* **`summary.csv`**: A human-readable spreadsheet containing aggregated seller performance
data, including revenue, delivery scores, and customer ratings.
* **`detail.parquet`**: A compressed, columnar data file containing the full scored dataset,
optimized for high-speed analysis and machine learning ingestion.
* **`chart.html`**: An interactive Altair visualization showing revenue distribution across
sellers. Open in any web browser — hover over bars to see exact figures.
* **`report.xlsx`**: A formatted Excel workbook containing the full stakeholder deliverable
with 5 sheets, embedded charts, and an executive narrative.

## Validation Checks

The pipeline runs a Pre-Flight check via `validation.py` before any SQL processing occurs:

1. **Schema Check**: Verifies that all 9 standard Olist tables are present in the DuckDB file.
2. **Key Integrity**: Confirms that critical columns like `order_id` and `seller_id` are not
entirely NULL.
3. **Temporal Sanity**: Ensures purchase timestamps are not empty and do not contain
future-dated entries.
4. **Volume Check**: Verifies the dataset contains a minimum threshold of rows (1,000+) to
ensure the database is not truncated.

**Failure Policy:** We use a Soft-Fail approach. If a check fails, the pipeline logs a WARNING
or ERROR via Loguru but continues execution. This allows the team to inspect partial or
corrupted data for debugging purposes rather than being completely blocked.

## Analysis Summary

Our analytical focus is on the Seller Performance Scorecard and Delivery Reliability across
the Olist marketplace. Revenue is heavily concentrated among SP-based sellers — the top 20
sellers account for over 60% of total platform revenue, consistent with a classic Pareto
distribution. Delivery performance varies significantly by region, with northern states missing
estimates by nearly 21 days on average. Customer ratings average 4.09 out of 5 across the top
100 sellers. This pipeline provides a scalable framework to dynamically segment vendors across
timeframes and geographic states, enabling data-driven decisions for marketplace logistics.

## Limitations & Caveats

* **Memory Constraints**: The pipeline uses `.fetchall()` for local environment compatibility,
which loads entire query results into RAM. It may struggle with datasets exceeding 10M+ rows.
* **Local Database Dependency**: The script expects `olist.duckdb` to be locally present in
the `data/` folder and does not support remote cloud database connections.
* **Input Sensitivity**: The `--start-date` parameter requires a strict `YYYY-MM-DD` format.
Incorrectly formatted strings will raise a `ValueError`.
* **Schema Rigidity**: The validation layer is hardcoded to the Olist schema. Structural
changes or table renaming will trigger validation warnings.

## Final Deliverable

**Format:** Excel Workbook (`output/report.xlsx`)

**Why Excel:** Recipients can open it with no installation required. The workbook is
self-contained with formatted tables, embedded charts, and narrative prose — everything a
manager needs in a single file.

**Sheets:**
- **Executive Summary** — key metrics, business overview, and actionable findings with
recommendations
- **Seller Scorecard** — full dataset of all 100 seller performance metrics including revenue,
delivery score, customer rating, and rank
- **Revenue Chart** — bar chart of top 20 sellers by revenue illustrating Pareto concentration
- **Delivery Trends** — line chart comparing delivery reliability across all 27 Brazilian states
- **Rating by State** — bar chart of average customer satisfaction scores by seller state

**To open:** Run `uv run wvu-ieng-331-final-19`, then open `output/report.xlsx` in Excel or
Google Sheets.
