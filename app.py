import streamlit as st
import subprocess
import sys
from pathlib import Path
import json
import pandas as pd

st.set_page_config(
    page_title="Multi-Source Web Scraping Pipeline",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Multi-Source Web Scraping & Data Consolidation")
st.write(
    "Scrape, clean, validate, deduplicate and consolidate data "
    "from multiple web sources."
)

st.markdown("---")

st.subheader("Available Sources")

col1, col2 = st.columns(2)

with col1:
    st.info("📚 Books to Scrape")

with col2:
    st.info("💬 Quotes to Scrape")

st.markdown("---")

st.subheader("Run Scraping Pipeline")

skip_details = st.checkbox(
    "Skip individual book detail pages",
    value=False
)

if st.button("🚀 Start Scraping", type="primary"):

    command = [sys.executable, "main.py"]

    if skip_details:
        command.append("--skip-book-details")

    with st.spinner("Running scraping pipeline... Please wait."):

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

    if result.returncode == 0:

        st.success("✅ Scraping pipeline completed successfully!")

        if result.stdout:
            st.subheader("Pipeline Output")
            st.code(result.stdout)

        output_dir = Path("output")

        csv_file = output_dir / "final_dataset.csv"
        report_file = output_dir / "summary_report.json"

        if csv_file.exists():

            df = pd.read_csv(csv_file)

            st.subheader("📊 Final Dataset")

            st.write(
                f"Total records collected: **{len(df)}**"
            )

            st.dataframe(
                df,
                use_container_width=True
            )

            st.download_button(
                label="⬇️ Download Final Dataset",
                data=csv_file.read_bytes(),
                file_name="final_dataset.csv",
                mime="text/csv"
            )

        if report_file.exists():

            st.subheader("📋 Summary Report")

            with open(report_file, "r", encoding="utf-8") as f:
                report = json.load(f)

            totals = report.get("totals", {})

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Raw Records",
                    totals.get("raw_records_collected", 0)
                )

            with c2:
                st.metric(
                    "Rejected",
                    totals.get("records_rejected", 0)
                )

            with c3:
                st.metric(
                    "Duplicates",
                    totals.get("duplicates_detected", 0)
                )

            with c4:
                st.metric(
                    "Final Records",
                    totals.get("final_records", 0)
                )

            with st.expander("View Complete Summary Report"):
                st.json(report)

    else:

        st.error("❌ The scraping pipeline failed.")

        if result.stderr:
            st.subheader("Error Details")
            st.code(result.stderr)