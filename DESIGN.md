# Design Rationale

## Parameter Flow

When our pipeline runs a parameterized report, the variables follow a structured path from the main script down to the database.

Using the Seller Scorecard as an example, if we want to filter by the state of São Paulo (`SP`), the process works like this:
1. Orchestrator (`pipeline.py`)
   In the `run_pipeline()` function, we define the state when calling the query:
   `get_seller_performance_scorecard(db_path, state="SP")`.

2. Data Access Layer (`queries.py`)
   This function takes in the `state` parameter, puts it into a list, and passes it into the execution function:
   `_execute_query(db_path, "seller_performance_scorecard.sql", [state])`.

3. Execution Engine (`_execute_query`)
   This function reads the SQL file and runs it using DuckDB:
   `conn.execute(query, params)`.
   DuckDB automatically maps `"SP"` to the `$1` placeholder in the SQL file.

## SQL Parameterization

Using `seller_performance_scorecard.sql` as our example:

- The SQL includes a condition like:
  `WHERE seller_state = $1`, where `$1` is a placeholder.

- In `queries.py`, `_execute_query` reads the SQL file as text and passes both the query and parameters into DuckDB. DuckDB safely inserts the values into the placeholders.

- We used parameterized queries instead of f-strings because of SQL injection risks. For example, if we used something like:
  `f"WHERE seller_state = '{state}'"`,
  a bad input could change the entire query. Parameterized queries avoid this by treating inputs as values only.

- We also chose to store SQL in `.sql` files instead of Python strings because it keeps things cleaner and easier to manage. It also makes it easier to test queries separately if needed.

## Validation Logic

We created a `validation.py` module to run checks on the database before the pipeline runs.

- Table Existence Check
  What it does: Uses `SHOW TABLES` to make sure all required tables exist.
  Why: Prevents crashes later if a table is missing.

- Key Columns NOT NULL
  What it does: Checks that important columns like `order_id` and `product_id` aren’t empty.
  Why: These are needed for joins and grouping.

- Date Range Validation
  What it does: Makes sure `order_purchase_timestamp` isn’t empty or in the future.
  Why: Future dates usually mean something is wrong with the data.

- Volume Threshold (>1,000 rows)
  What it does: Ensures tables have enough data.
  Why: If a table has very few rows, it likely wasn’t loaded correctly.

Failure Handling:
If a check fails, the pipeline does not stop. Instead, we log a warning using `loguru`. We decided this so users can still run the pipeline and debug issues instead of being completely blocked.

## Error Handling

We added specific exception handling so errors are easier to understand.

- FileNotFoundError in `_execute_query`
  Catches: Missing SQL files or database file
  Action: Raises a clear error message showing which file path is wrong

- duckdb.Error in `_execute_query`
  Catches: SQL errors or database issues
  Action: Wraps the error with extra info about which SQL file caused it

- Why we avoided `except:`
  Using a general `except:` would catch everything, including `KeyboardInterrupt`. That would make it hard to stop the program and also hide useful error messages.

## Scaling & Adaptation

1. Handling 10 Million Orders
   If the dataset increased to 10 million rows, the main issue would be in `_execute_query`. Right now, we use `.fetchall()`, which loads everything into a Python list. This would likely cause memory issues.

   A better approach would be to use `cursor.pl()` with `pyarrow`, which allows data to be transferred more efficiently into Polars without loading everything into memory at once.

2. Adding JSON Output
   If we wanted to also export JSON files, we could update `pipeline.py`. After writing the CSV file, we could add:
   `df.write_json(output_dir / filename.replace('.csv', '.json'))`.

   Since the data is already in a clean DataFrame, this change would be simple and wouldn’t require changes to other parts of the system.
