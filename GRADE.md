# Final Deliverable Grade

**Team 19 (Audrey Doyle, Ian Donnen, Rylee Lindermuth)**

| Criterion | Score | Max |
|-----------|------:|----:|
| Deliverable Quality | 6 | 6 |
| Visualizations | 4 | 6 |
| Pipeline Integration | 6 | 6 |
| Analytical Narrative | 6 | 6 |
| **Total (rubric portion)** | **22** | **24** |

Video walkthrough graded separately.

## Deliverable Quality (6/6)

`output/report.xlsx` is a five-sheet Excel workbook (Executive Summary, Seller Scorecard, Revenue Chart, Delivery Trends, Rating by State). Executive Summary has Key Metrics tiles (total sellers, total revenue, avg customer rating) plus a substantial Key Findings paragraph. Each subsequent sheet has its own data table and embedded native Excel chart. Workbook is well-organised and opens without setup.

## Visualizations (4/6)

Three native Excel charts:

- **Top 20 Sellers by Revenue** (bar, categorical) - well-typed.
- **Delivery Trends** (line) - the underlying data is per-state delivery delay; using a line chart implies temporal continuity between states that does not exist. Should be a bar chart.
- **Average Customer Rating by Seller State** (bar, categorical) - well-typed.

Spec required at least one temporal chart. None of the three are temporal (the line chart is line-typed but plots categorical state data, not a time series), so the temporal requirement is unmet. The chart-type mismatch on Delivery Trends is the same issue.

## Pipeline Integration (6/6)

`uv run wvu-ieng-331-final-19` after `uv sync` runs the full pipeline end-to-end with defaults. Tested with the extended database; pipeline ran cleanly with one validation warning (missing `product_category_name_translation` table in the extended DB) and produced summary.csv, detail.parquet, chart.html, and report.xlsx. Output filenames match the spec.

## Analytical Narrative (6/6)

Executive Summary's Key Findings paragraph is dense with specific data: top 20 sellers account for over 60% of platform revenue (classic Pareto, supply chain risk if key sellers exit), northern states (AM, RO, AC) miss estimates by nearly 21 days on average vs AL/SP performing closest to promised dates, average rating 4.09 with outliers below 3.5 warranting investigation. Two concrete next steps close the narrative: cross-reference delivery performance with customer ratings to find logistics-driven dissatisfaction, and geographic diversification to reduce SP revenue concentration risk. Reads as a professional brief.
