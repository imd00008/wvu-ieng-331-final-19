from pathlib import Path

import duckdb
import polars as pl


def _execute_query(db_path: str, sql_filename: str, params: list) -> pl.DataFrame:
    """Helper function to execute SQL WITHOUT needing pyarrow."""
    current_dir = Path(__file__).parent
    sql_file_path = current_dir.parent.parent / "sql" / sql_filename

    if not sql_file_path.exists():
        raise FileNotFoundError(f"Could not find the SQL file at: {sql_file_path}")
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found at: {db_path}")

    query = sql_file_path.read_text()
    conn = duckdb.connect(db_path)

    try:
        # 1. Execute the query
        cursor = conn.execute(query, params)

        # 2. Fetch the data as a plain Python list (no Arrow needed)
        data = cursor.fetchall()

        # 3. Get the column names so the table isn't just numbers
        columns = [desc[0] for desc in cursor.description]

        # 4. Hand the raw list to Polars manually
        return pl.DataFrame(data, schema=columns, orient="row")

    except duckdb.Error as e:
        raise duckdb.Error(f"Failed to execute {sql_filename}: {e}")
    finally:
        conn.close()


def get_abc_classification(db_path: str, category: str = None) -> pl.DataFrame:
    """
    Executes the ABC inventory classification query.

    Args:
        db_path (str): The DuckDB file path.
        category (str, optional): Product category to filter by. Defaults to None.

    Returns:
        pl.DataFrame
    """
    return _execute_query(db_path, "abc_inventory_classification.sql", [category])


def get_cohort_retention(
    db_path: str, start_date: str = None, end_date: str = None
) -> pl.DataFrame:
    """
    Executes the cohort retention analysis based on acquisition dates.

    Args:
        db_path (str): The DuckDB file path.
        start_date (str, optional): YYYY-MM-DD start of cohort. Defaults to None.
        end_date (str, optional): YYYY-MM-DD end of cohort. Defaults to None.

    Returns:
        pl.DataFrame
    """
    return _execute_query(
        db_path, "cohort_retention_analysis.sql", [start_date, end_date]
    )


def get_data_audit(
    db_path: str, start_date: str = None, end_date: str = None
) -> pl.DataFrame:
    """
    Executes the data quality audit.

    Args:
        db_path (str): The DuckDB file path.
        start_date (str, optional): Start date for audit window. Defaults to None.
        end_date (str, optional): End date for audit window. Defaults to None.

    Returns:
        pl.DataFrame
    """
    return _execute_query(db_path, "data_audit.sql", [start_date, end_date])


def get_delivery_time_by_geography(
    db_path: str, start_date: str = None, end_date: str = None
) -> pl.DataFrame:
    """
    Executes the geographic delivery delay analysis.

    Args:
        db_path (str): The DuckDB file path.
        start_date (str, optional): Start date for order window. Defaults to None.
        end_date (str, optional): End date for order window. Defaults to None.

    Returns:
        pl.DataFrame
    """
    return _execute_query(
        db_path, "delivery_time_by_geography.sql", [start_date, end_date]
    )


def get_seller_performance_scorecard(db_path: str, state: str = None) -> pl.DataFrame:
    """
    Executes the seller performance scorecard.

    Args:
        db_path (str): The DuckDB file path.
        state (str, optional): 2-letter seller state code (e.g., 'SP'). Defaults to None.

    Returns:
        pl.DataFrame
    """
    return _execute_query(db_path, "seller_performance_scorecard.sql", [state])


# ==========================================
# TESTING BLOCK
# ==========================================
if __name__ == "__main__":
    # Adjust this path if your DuckDB file is named differently!
    TEST_DB = "data/olist.duckdb"

    print("=== Testing Data Access Layer ===\n")

    try:
        print("1. Testing ABC Classification (Unfiltered)...")
        print(get_abc_classification(TEST_DB).head(3))

        print("\n2. Testing Cohort Retention (Q1 2018)...")
        print(get_cohort_retention(TEST_DB, "2018-01-01", "2018-03-31"))

        print("\n3. Testing Data Audit (Full)...")
        print(get_data_audit(TEST_DB))

        print("\n4. Testing Delivery Geo Analysis (Unfiltered)...")
        print(get_delivery_time_by_geography(TEST_DB).head(3))

        print("\n5. Testing Seller Scorecard (State: SP)...")
        print(get_seller_performance_scorecard(TEST_DB, state="SP").head(3))

        print("\n ALL QUERIES EXECUTED SUCCESSFULLY!")

    except Exception as e:
        print(f"\n ERROR OCCURRED: {e}")
