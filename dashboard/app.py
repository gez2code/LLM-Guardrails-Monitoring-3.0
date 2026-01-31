"""
LLM Monitoring Dashboard - Main Application
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import time
from datetime import datetime

from dashboard import config
from dashboard.data.loader import DataLoader
from dashboard.data.processor import DataProcessor
from dashboard.components.metrics import render_metric_cards, render_alert_metrics
from dashboard.components.filters import render_sidebar, render_data_info
from dashboard.components.charts import (
    render_time_series,
    render_label_distribution,
    render_severity_pie,
    render_danger_pie,
    render_score_heatmap
)
from dashboard.components.tables import render_violations_table, render_alerts_table



# Page configuration
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT
)


def main():
    """Main application entry point"""

    # Title
    st.title(f"{config.PAGE_ICON} LLM Monitoring Dashboard")
    st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize data loader
    loader = DataLoader()

    # Render sidebar filters
    filters = render_sidebar()

    # Show data file info in sidebar
    file_stats = loader.get_file_stats()
    render_data_info(file_stats)

    # Load data
    with st.spinner("Loading data..."):
        violations_df = loader.load_violations(source=filters.get('source', 'both'))
        alerts_df = loader.load_alerts()

    # Apply filters to violations
    filtered_violations = DataProcessor.filter_data(violations_df, **filters)

    # Main content area
    st.header("Overview")

    # Metric cards
    render_metric_cards(filtered_violations, alerts_df)

    st.divider()

    # Time series charts
    st.header("Trends")

    col1, col2 = st.columns(2)

    with col1:
        render_time_series(
            filtered_violations,
            title="Violations Over Time",
            color_column="severity",
            freq=filters.get('time_aggregation', 'H')
        )

    with col2:
        render_time_series(
            alerts_df,
            title="Alerts Over Time",
            color_column="danger_level",
            freq=filters.get('time_aggregation', 'H')
        )

    st.divider()

    # Distribution charts
    st.header("Analysis")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        render_label_distribution(filtered_violations)

    with col2:
        render_severity_pie(filtered_violations)

    with col3:
        render_danger_pie(alerts_df)

    st.divider()

    # Score heatmap (collapsible)
    with st.expander("Toxicity Score Heatmap (Last 20 Violations)", expanded=False):
        render_score_heatmap(filtered_violations.tail(20))

    st.divider()

    # Data tables
    st.header("Data")

    tab1, tab2 = st.tabs(["Violations", "Alerts"])

    with tab1:
        render_violations_table(filtered_violations, page_size=config.DEFAULT_PAGE_SIZE)

    with tab2:
        render_alerts_table(alerts_df, page_size=config.DEFAULT_PAGE_SIZE)

    # Auto-refresh
    if filters.get('auto_refresh', False):
        refresh_interval = filters.get('refresh_interval', config.DEFAULT_REFRESH_INTERVAL)
        time.sleep(refresh_interval)
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
