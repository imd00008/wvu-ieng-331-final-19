# Milestone 2: Python Pipeline

**Team 19**: Ian Donnen, Audrey Doyle, Rylee Lindermuth

## Overview
This repository contains an automated, parameterizable Python data pipeline developed to analyze the Olist e-commerce dataset. Managed via uv, the system performs pre-flight data validation, executes parameterized DuckDB SQL queries, and uses Polars to process dynamic command-line filters. The pipeline ultimately generates scalable business intelligence, outputting summary CSVs, machine-readable Parquet files, and interactive Altair visualizations.

## How to Run

Instructions to run the pipeline from a fresh clone:

```bash
git clone https://github.com/imd00008/wvu-ieng-331-m2-19.git
cd wvu-ieng-331-m2-19
uv sync
# place olist.duckdb in the data/ directory
uv run wvu-ieng-331-m2-19
uv run wvu-ieng-331-m2-19 --start-date 2017-01-01 --seller-state SP
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--start-date` | string | None (no filter) | Filters orders to only include those purchased on or after the provided date (Format: YYYY-MM-DD). |
| `--seller-state` | string | None (no filter) | Filters the analysis to a specific Brazilian state using its 2-letter abbreviation (e.g., SP, RJ, MG). |

## Outputs

All generated reports are stored in the `output/` directory:

* **`summary.csv`**: A human-readable spreadsheet containing aggregated performance data. It summarizes total revenue and order counts per seller, allowing for quick identification of top earners.
* **`detail.parquet`**: A compressed, columnar data file containing the full scored dataset. This is the "system-ready" version of the data, optimized for high-speed analysis and machine learning ingestion.
* **`chart.html`**: An interactive Altair visualization. Open this in any web browser to see the revenue distribution across sellers; users can hover over specific bars to see exact revenue figures and shortened Seller IDs.

## Validation Checks

The pipeline runs a "Pre-Flight" check via `validation.py` before any SQL processing occurs:

1.  **Schema Check**: Verifies that all 9 standard Olist tables are present in the DuckDB file.
2.  **Key Integrity**: Confirms that critical columns like `order_id` and `seller_id` are not entirely NULL.
3.  **Temporal Sanity**: Ensures purchase timestamps are not empty and do not contain future-dated entries.
4.  **Volume Check**: Verifies the dataset contains a minimum threshold of rows (1,000+) to ensure the database isn't truncated.

**Failure Policy:** We utilize a **Soft-Fail** approach. If a check fails, the pipeline logs a `WARNING` or `ERROR` via Loguru but continues execution. This allows the team to inspect partial or corrupted data for debugging purposes.

## Analysis Summary

Our analytical focus remains on the **Seller Performance Scorecard** within the Olist marketplace. The data shows a massive revenue concentration in the São Paulo (SP) region, following a classic Pareto (80/20) distribution where a small number of "A-Class" sellers generate the majority of platform value. This automated pipeline provides a scalable analytical framework to dynamically segment these high-performing vendors across different timeframes and geographic states, enabling data-driven decisions for marketplace logistics.

## Limitations & Caveats

* **Memory Constraints**: The pipeline currently uses a `.fetchall()` method to ensure compatibility with local environments, which loads the entire query result into RAM. It may struggle with datasets exceeding 10M+ rows on machines with low memory.
* **Local Database Dependency**: The script expects `olist.duckdb` to be locally present in the `data/` folder and does not currently support remote cloud database connections.
* **Input Sensitivity**: The `--start-date` parameter requires a very specific `YYYY-MM-DD` format. Providing an incorrectly formatted string will cause a `ValueError`.
* **Schema Rigidity**: The validation layer is hardcoded to the Olist schema. Any structural changes or renaming of tables in the source database will trigger validation warnings.
