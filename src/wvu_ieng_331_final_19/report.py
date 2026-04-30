from pathlib import Path

import polars as pl
import xlsxwriter
from loguru import logger


def generate_report(
    seller_df: pl.DataFrame,
    delivery_df: pl.DataFrame,
    output_dir: Path,
    seller_state: str = None,
) -> None:
    """
    Generates a formatted Excel report from pipeline outputs.

    Args:
        seller_df (pl.DataFrame): Seller performance scorecard DataFrame.
        delivery_df (pl.DataFrame): Delivery time by geography DataFrame.
        output_dir (Path): Directory to write the report file.
        seller_state (str, optional): State filter label for report title.

    Returns:
        None
    """
    report_path = output_dir / "report.xlsx"
    state_label = seller_state or "All States"

    try:
        workbook = xlsxwriter.Workbook(str(report_path))

        # ── Formats ──────────────────────────────────────────
        header_fmt = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#003366",
                "font_color": "#FFFFFF",
                "border": 1,
                "align": "center",
            }
        )
        number_fmt = workbook.add_format({"num_format": "#,##0.00", "border": 1})
        cell_fmt = workbook.add_format({"border": 1})
        title_fmt = workbook.add_format({"bold": True, "font_size": 14})

        # ── Sheet 1: Executive Summary ────────────────────────
        ws_summary = workbook.add_worksheet("Executive Summary")
        ws_summary.write(
            "A1", f"Olist Supply Chain Analysis — {state_label}", title_fmt
        )
        ws_summary.write(
            "A3",
            "This report analyzes seller performance across the Olist "
            "Brazilian e-commerce platform. Key findings cover revenue distribution, "
            "delivery reliability, and customer satisfaction by seller.",
        )
        ws_summary.write("A5", "Key Metrics", workbook.add_format({"bold": True}))
        ws_summary.write("A6", "Total Sellers Analyzed:")
        ws_summary.write("B6", len(seller_df))
        ws_summary.write("A7", "Total Revenue:")
        ws_summary.write("B7", float(seller_df["revenue"].sum()), number_fmt)
        ws_summary.write("A8", "Avg Customer Rating:")
        ws_summary.write("B8", round(float(seller_df["customer_rating"].mean()), 2))
        ws_summary.set_column("A:A", 30)
        ws_summary.set_column("B:B", 20)
        ws_summary.write("A10", "Key Findings", workbook.add_format({"bold": True}))
        ws_summary.write(
            "A11",
            "Revenue is heavily concentrated among SP-based sellers — the top 20 sellers "
            "account for over 60% of total platform revenue, a classic Pareto distribution "
            "that creates significant supply chain risk if key sellers exit. Delivery "
            "performance varies widely by region: northern states (AM, RO, AC) miss estimates "
            "by nearly 21 days on average, while AL and SP perform closest to their promised "
            "dates. Customer ratings average 4.09 out of 5 across the top 100 sellers, "
            "suggesting general satisfaction, but outliers scoring below 3.5 warrant "
            "investigation. Recommended next steps: cross-reference delivery underperformance "
            "with low customer ratings to identify whether logistics failures are driving "
            "dissatisfaction, and assess geographic diversification to reduce SP revenue "
            "concentration risk.",
        )
        ws_summary.set_row(10, 100)
        wrap_fmt = workbook.add_format({"text_wrap": True})
        ws_summary.set_column("A:A", 80, wrap_fmt)

        # ── Sheet 2: Seller Scorecard Data ───────────────────
        ws_data = workbook.add_worksheet("Seller Scorecard")
        columns = seller_df.columns
        for col_idx, col_name in enumerate(columns):
            ws_data.write(0, col_idx, col_name, header_fmt)
        for row_idx, row in enumerate(seller_df.iter_rows(), start=1):
            for col_idx, value in enumerate(row):
                if isinstance(value, float):
                    ws_data.write(row_idx, col_idx, value, number_fmt)
                else:
                    ws_data.write(row_idx, col_idx, value, cell_fmt)
        ws_data.set_column(0, len(columns) - 1, 18)

        # ── Sheet 3: Chart ────────────────────────────────────
        ws_chart = workbook.add_worksheet("Revenue Chart")
        ws_chart.write("A1", "Top 20 Sellers by Revenue", title_fmt)
        ws_chart.write(
            "A2",
            "This chart compares total revenue across the top 20 sellers. "
            "A small number of sellers drive the majority of revenue, "
            "consistent with the Pareto principle.",
        )

        # Write chart data (top 20 sellers by revenue)
        top20 = seller_df.sort("revenue", descending=True).head(20)
        ws_chart.write("A4", "Seller ID", header_fmt)
        ws_chart.write("B4", "Revenue", header_fmt)
        for i, row in enumerate(top20.iter_rows(named=True), start=4):
            ws_chart.write(i, 0, str(row["seller_id"])[:8], cell_fmt)
            ws_chart.write(i, 1, float(row["revenue"]), number_fmt)

        bar_chart = workbook.add_chart({"type": "bar"})
        bar_chart.add_series(
            {
                "name": "Revenue",
                "categories": ["Revenue Chart", 4, 0, 4 + len(top20) - 1, 0],
                "values": ["Revenue Chart", 4, 1, 4 + len(top20) - 1, 1],
            }
        )
        bar_chart.set_title({"name": f"Top 20 Sellers by Revenue ({state_label})"})
        bar_chart.set_x_axis({"name": "Total Revenue (BRL)"})
        bar_chart.set_y_axis({"name": "Seller ID"})
        bar_chart.set_size({"width": 720, "height": 480})
        ws_chart.insert_chart("D4", bar_chart)

        # ── Sheet 4: Delivery Trends ──────────────────────────
        ws_trend = workbook.add_worksheet("Delivery Trends")
        ws_trend.write("A1", "Delivery Performance by State", title_fmt)
        ws_trend.write(
            "A2",
            "This chart shows how far off actual deliveries are from "
            "estimates by state. Negative values mean deliveries arrived "
            "earlier than promised. States closer to 0 are least reliable "
            "relative to their estimates.",
            cell_fmt,
        )

        ws_trend.write("A4", "Rank", header_fmt)
        ws_trend.write("B4", "State", header_fmt)
        ws_trend.write("C4", "Avg Days Off Estimate", header_fmt)
        ws_trend.write("D4", "Total Orders", header_fmt)

        for i, row in enumerate(delivery_df.iter_rows(named=True), start=4):
            ws_trend.write(i, 0, row["national_unreliability_rank"], cell_fmt)
            ws_trend.write(i, 1, row["customer_state"], cell_fmt)
            ws_trend.write(i, 2, row["avg_days_off_estimate"], number_fmt)
            ws_trend.write(i, 3, row["total_orders_analyzed"], cell_fmt)

        line_chart = workbook.add_chart({"type": "line"})
        line_chart.add_series(
            {
                "name": "Avg Days Off Estimate",
                "categories": ["Delivery Trends", 4, 1, 4 + len(delivery_df) - 1, 1],
                "values": ["Delivery Trends", 4, 2, 4 + len(delivery_df) - 1, 2],
            }
        )
        line_chart.set_title(
            {"name": "Delivery Reliability by State (Days Off Estimate)"}
        )
        line_chart.set_x_axis({"name": "State"})
        line_chart.set_y_axis({"name": "Avg Days Off Estimate"})
        line_chart.set_size({"width": 720, "height": 480})
        ws_trend.insert_chart("F4", line_chart)
        ws_trend.set_column("A:A", 10)
        ws_trend.set_column("B:B", 10)
        ws_trend.set_column("C:C", 22)
        ws_trend.set_column("D:D", 15)

        # ── Sheet 5: Customer Rating by State ─────────────────
        ws_rating = workbook.add_worksheet("Rating by State")
        ws_rating.write("A1", "Average Customer Rating by Seller State", title_fmt)
        ws_rating.write(
            "A2",
            "This chart compares average customer satisfaction scores "
            "across seller states. States with lower ratings may indicate "
            "fulfillment or product quality issues worth investigating.",
            cell_fmt,
        )

        ws_rating.write("A4", "State", header_fmt)
        ws_rating.write("B4", "Avg Customer Rating", header_fmt)
        ws_rating.write("C4", "Seller Count", header_fmt)

        state_ratings = (
            seller_df.group_by("seller_state")
            .agg(
                [
                    pl.col("customer_rating").mean().alias("avg_rating"),
                    pl.col("seller_id").count().alias("seller_count"),
                ]
            )
            .sort("avg_rating", descending=True)
        )

        for i, row in enumerate(state_ratings.iter_rows(named=True), start=4):
            ws_rating.write(i, 0, row["seller_state"], cell_fmt)
            ws_rating.write(i, 1, round(float(row["avg_rating"]), 2), number_fmt)
            ws_rating.write(i, 2, row["seller_count"], cell_fmt)

        rating_chart = workbook.add_chart({"type": "bar"})
        rating_chart.add_series(
            {
                "name": "Avg Customer Rating",
                "categories": ["Rating by State", 4, 0, 4 + len(state_ratings) - 1, 0],
                "values": ["Rating by State", 4, 1, 4 + len(state_ratings) - 1, 1],
            }
        )
        rating_chart.set_title({"name": "Average Customer Rating by Seller State"})
        rating_chart.set_x_axis({"name": "Avg Rating (1-5)", "min": 0, "max": 5})
        rating_chart.set_y_axis({"name": "Seller State"})
        rating_chart.set_size({"width": 720, "height": 480})
        ws_rating.insert_chart("E4", rating_chart)
        ws_rating.set_column("A:A", 10)
        ws_rating.set_column("B:B", 22)
        ws_rating.set_column("C:C", 15)

        workbook.close()
        logger.success(f"📋 Report saved to {report_path}")

    except OSError as e:
        logger.error(f"❌ Could not write report file: {e}")
