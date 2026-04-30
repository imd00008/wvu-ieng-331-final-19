import argparse
import sys
from pathlib import Path

import altair as alt
import duckdb
import polars as pl
from loguru import logger

from .queries import get_seller_performance_scorecard
from .validation import run_pre_flight_checks, validate_dataframe


def main() -> None:
    """
    Main entry point for the IENG 331 data pipeline.
    Parses CLI arguments, orchestrates validation, runs queries, and exports reports.

    Args:
        None (Arguments are parsed directly from the command line via argparse).

    Returns:
        None (Outputs are saved directly to the file system).
    """
    # 1. ARGPARSE: The Steering Wheel
    parser = argparse.ArgumentParser(description="Zelyria E-commerce Data Pipeline")
    parser.add_argument(
        "--seller-state",
        type=str,
        default=None,
        help="Filter analysis by a specific seller state (e.g., SP)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Filter orders starting from this date (YYYY-MM-DD)",
    )

    args = parser.parse_args()

    logger.info(
        f"🚀 Starting Pipeline with arguments: State={args.seller_state}, Start={args.start_date}"
    )

    db_path = "data/olist.duckdb"
    output_dir = Path("output")

    # 2. OUTPUT FOLDER CREATION & OSERROR HANDLING
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"❌ Fatal Error: Could not create output directory. {e}")
        sys.exit(1)

    # 3. PRE-FLIGHT VALIDATION
    logger.info("🔍 Running Database Pre-Flight Validation...")
    if not run_pre_flight_checks(db_path):
        logger.warning("⚠️ Pipeline continuing despite validation warnings.")

    # 4. QUERY & EXPORT WITH ERROR HANDLING
    logger.info("⚙️ Executing Queries and Generating Reports...")
    try:
        # Pass the parsed arguments into your query function
        # (Assuming your query function was built to accept these parameters)
        df = get_seller_performance_scorecard(db_path, state=args.seller_state)

        # If the user passed bad data (e.g., a state number instead of letters), raise ValueError
        if args.seller_state and len(args.seller_state) != 2:
            raise ValueError("Seller state must be a 2-letter abbreviation.")

        if validate_dataframe(df, "Seller Scorecard"):
            # A. SUMMARY.CSV Output
            csv_path = output_dir / "summary.csv"
            df.write_csv(csv_path)
            logger.success(f"💾 Saved {csv_path}")

            # B. DETAIL.PARQUET Output
            parquet_path = output_dir / "detail.parquet"
            df.write_parquet(parquet_path)
            logger.success(f"📦 Saved {parquet_path}")

            # C. CHART.HTML Output (Using Altair)
            # Altair natively supports Polars DataFrames
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("seller_id:N", title="Seller ID"),
                    y=alt.Y("revenue:Q", title="Total Revenue"),
                )
                .properties(
                    title=f"Seller Revenue Distribution (State: {args.seller_state or 'ALL'})",
                    width=800,
                    height=400,
                )
            )
            html_path = output_dir / "chart.html"
            chart.save(html_path)
            logger.success(f"📊 Saved {html_path}")

    # Specific Exception Handling defined by the rubric
    except FileNotFoundError as e:
        logger.error(
            f"❌ Database file missing. Please check the /data folder. Details: {e}"
        )
    except duckdb.Error as e:
        logger.error(f"❌ SQL Execution crashed inside DuckDB. Details: {e}")
    except ValueError as e:
        logger.error(f"❌ Invalid parameter input detected. Details: {e}")
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
