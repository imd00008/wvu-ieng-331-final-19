from datetime import datetime

import duckdb
import polars as pl
from loguru import logger


def run_pre_flight_checks(db_path: str) -> bool:
    """
    Runs pre-analysis validation on the raw DuckDB database.
    Checks for table existence, nulls in key columns, date ranges, and row counts.
    """
    logger.info("🔍 Starting Pre-Flight Database Validation...")
    passed_all = True

    try:
        conn = duckdb.connect(db_path)

        # 1. Verify all 9 expected tables exist
        expected_tables = {
            "customers",
            "geolocation",
            "order_items",
            "order_payments",
            "order_reviews",
            "orders",
            "products",
            "sellers",
            "product_category_name_translation",
        }
        # Get actual tables from DuckDB
        actual_tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
        missing_tables = expected_tables - actual_tables

        if missing_tables:
            logger.warning(f"⚠️ Missing expected tables: {missing_tables}")
            passed_all = False
        else:
            logger.success("✅ All 9 expected Olist tables exist.")

        # 2. Key columns not entirely NULL
        # SQL COUNT() ignores nulls, so if COUNT is 0, the column is entirely NULL
        key_checks = {
            "orders": "order_id",
            "customers": "customer_id",
            "products": "product_id",
            "sellers": "seller_id",
        }
        for table, col in key_checks.items():
            if table in actual_tables:
                count_valid = conn.execute(
                    f"SELECT COUNT({col}) FROM {table}"
                ).fetchone()[0]
                if count_valid == 0:
                    logger.warning(
                        f"⚠️ Key column '{col}' in table '{table}' is entirely NULL!"
                    )
                    passed_all = False

        # 3. Date range in orders is reasonable (not empty, not future-dated)
        if "orders" in actual_tables:
            dates = conn.execute(
                "SELECT MIN(order_purchase_timestamp), MAX(order_purchase_timestamp) FROM orders"
            ).fetchone()

            if dates[0] is None or dates[1] is None:
                logger.warning("⚠️ orders.order_purchase_timestamp is completely empty!")
                passed_all = False
            elif type(dates[1]) is str:  # Handle string parsing just in case
                max_date = datetime.strptime(dates[1][:19], "%Y-%m-%d %H:%M:%S")
                if max_date > datetime.now():
                    logger.warning(
                        f"⚠️ orders table contains future dates! (Max: {max_date})"
                    )
                    passed_all = False
            elif dates[1] > datetime.now():
                logger.warning(
                    f"⚠️ orders table contains future dates! (Max: {dates[1]})"
                )
                passed_all = False

        # 4. Row counts for core tables exceed threshold (1,000 rows)
        core_tables = ["orders", "order_items", "customers"]
        for table in core_tables:
            if table in actual_tables:
                row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if row_count < 1000:
                    logger.warning(
                        f"⚠️ Table '{table}' has only {row_count} rows! (Expected > 1000)"
                    )
                    passed_all = False

        if passed_all:
            logger.success("🚀 Database passed all Pre-Flight checks!")
        else:
            logger.warning("🛑 Database validation completed with WARNINGS.")

        return passed_all

    except Exception as e:
        logger.error(f"❌ Validation crashed: {e}")
        return False
    finally:
        if "conn" in locals():
            conn.close()


def validate_dataframe(df: pl.DataFrame, label: str) -> bool:
    """Performs a standard audit on an incoming Polars DataFrame."""
    if df.is_empty():
        logger.error(f"❌ VALIDATION FAILED: {label} returned 0 rows!")
        return False

    total_nulls = df.null_count().sum_horizontal()[0]
    if total_nulls > 0:
        logger.warning(
            f"⚠️ {label} contains {total_nulls} null values. Proceed with caution."
        )
    else:
        logger.success(f"✅ {label} passed integrity check ({len(df)} rows).")
    return True


# ==========================================
# TESTING BLOCK
# ==========================================
if __name__ == "__main__":
    test_db = "data/olist.duckdb"
    print("=== Testing Database Pre-Flight Checks ===")
    run_pre_flight_checks(test_db)
