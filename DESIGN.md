# Design Rationale

## Parameter Flow

When our pipeline runs a parameterized report, the variables follow a structured path from the
main script down to the database.

Using the Seller Scorecard as an example, if we want to filter by the state of São Paulo (`SP`),
the process works like this:

1. **Orchestrator (`pipeline.py`)** — The `main()` function parses `--seller-state SP` via
`argparse` and stores it as `args.seller_state`. It then passes this value into the query
function: `get_seller_performance_scorecard(db_path, state=args.seller_state)`.

2. **Data Access Layer (`queries.py`)** — `get_seller_performance_scorecard()` takes the
`state` parameter, wraps it in a list, and passes it to the execution helper:
`_execute_query(db_path, "seller_performance_scorecard.sql", [state])`.

3. **Execution Engine (`_execute_query`)** — This function reads the SQL file from the `sql/`
directory using `pathlib` and executes it against DuckDB:
`conn.execute(query, params)`. DuckDB maps `"SP"` to the `$1` placeholder in the SQL file.

4. **Report Layer (`report.py`)** — The resulting DataFrame is passed directly into
`generate_report(seller_df, delivery_df, output_dir, seller_state=args.seller_state)`, which
uses the state label in the report title and filters the Excel output accordingly.

## SQL Parameterization

Using `seller_performance_scorecard.sql` as our example:

- The SQL includes the condition `AND ($1 IS NULL OR s.seller_state = $1)`, where `$1` is a
placeholder. When `$1` is NULL, the filter is skipped and all states are returned. When a value
is provided, only that state's sellers are returned.

- In `queries.py`, `_execute_query` reads the `.sql` file as plain text using
`sql_file_path.read_text()` and passes both the query string and parameter list into DuckDB via
`conn.execute(query, params)`. DuckDB safely binds the values to the placeholders.

- We used parameterized queries instead of f-strings to prevent SQL injection. An f-string like
`f"WHERE seller_state = '{state}'"` would allow a malicious or malformed input to alter the
query structure. Parameterized queries treat inputs as values only, never as executable SQL.

- SQL lives in `.sql` files rather than inline Python strings because it keeps the codebase
clean and modular. It also allows queries to be read, tested, and modified independently of the
Python logic.

## Validation Logic

We created a `validation.py` module that runs `run_pre_flight_checks()` before any queries
execute.

- **Table Existence Check** — Uses `SHOW TABLES` in DuckDB to verify all 9 expected Olist
tables are present. Prevents downstream crashes from missing tables during joins.

- **Key Columns NOT NULL** — Checks that `order_id`, `customer_id`, `product_id`, and
`seller_id` have at least one non-NULL value using `COUNT(col)`. These columns are required
for every join in our SQL queries.

- **Date Range Validation** — Queries `MIN` and `MAX` of `order_purchase_timestamp` to confirm
the column is not empty and does not contain future-dated records. Future dates indicate a data
loading error.

- **Volume Threshold** — Verifies that `orders`, `order_items`, and `customers` each contain
more than 1,000 rows. A threshold of 1,000 was chosen because the real Olist dataset has
99,000+ rows — anything below 1,000 signals a truncated or corrupted load.

**Failure Handling:** All failures log a WARNING via `loguru` and set `passed_all = False`, but
the pipeline continues. This soft-fail approach lets us inspect partial data rather than being
completely blocked on a single missing table.

## Error Handling

We added specific exception types throughout the codebase so errors are actionable.

- **`FileNotFoundError` in `_execute_query`** — Catches a missing `.sql` file or missing
database file. Raises a clear message showing the exact path that was not found, so the user
knows immediately whether the database or the SQL file is the problem.

- **`duckdb.Error` in `_execute_query`** — Catches SQL execution failures inside DuckDB, such
as syntax errors or missing columns. Wraps the error with the name of the SQL file that caused
it so the user knows which query to investigate.

- **`ValueError` in `pipeline.py`** — Catches invalid parameter inputs, such as a
`--seller-state` value that is not exactly 2 characters. Logged at ERROR level before the
pipeline exits gracefully.

- **`OSError` in `pipeline.py` and `report.py`** — Catches file write failures, such as the
output directory being read-only or the Excel file being open in another program. Logged with
a clear message so the user knows to close the file or check permissions.

- **Why we avoided bare `except:`** — A bare `except:` catches everything including
`KeyboardInterrupt`, making it impossible to stop the program with Ctrl+C. It also hides the
actual error type, making debugging significantly harder.

## Scaling & Adaptation

1. **If the Olist dataset grew to 10 million orders**, the bottleneck would be in
`_execute_query`. The current `.fetchall()` call loads the entire result set into a Python list
before handing it to Polars. At 10M rows this would likely exhaust RAM. The fix would be to use
DuckDB's native `cursor.pl()` method, which transfers data directly into a Polars DataFrame via
Apache Arrow without materializing a Python list.

2. **If we needed to add a third output format (e.g., JSON)**, the change would be isolated to
`pipeline.py`. After the existing `df.write_csv()` call, we would add
`df.write_json(output_dir / "summary.json")`. Since the data is already in a clean Polars
DataFrame at that point, no changes to `queries.py`, `validation.py`, or `report.py` would be
needed.

## Report Module

The `report.py` module is called at the end of `pipeline.py` after all query outputs are
generated. It receives `seller_df` and `delivery_df` directly from the pipeline and writes a
formatted Excel workbook to `output/report.xlsx` using XlsxWriter.

The workbook contains 5 sheets: Executive Summary (narrative + key metrics), Seller Scorecard
(full dataset), Revenue Chart (bar chart of top 20 sellers), Delivery Trends (line chart by
state), and Rating by State (bar chart of average customer rating by state). Each sheet
includes a title, caption, formatted headers, and an embedded chart where applicable.

The workbook is regenerated on every pipeline run — it is not a manual export. Excel was chosen
because recipients can open it with no additional software, no terminal commands, and no
dependencies.
