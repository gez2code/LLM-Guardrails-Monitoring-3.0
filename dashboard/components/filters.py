"""Sidebar filter components"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any

from dashboard import config


# ------------------------------------------------------------------
# Main Sidebar
# ------------------------------------------------------------------

def render_sidebar() -> Dict[str, Any]:
    """
    Render sidebar filter controls (policy-aware)

    Returns:
        Dictionary of filter values
    """
    st.sidebar.header("Filters")

    filters: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Data source
    # ------------------------------------------------------------------

    filters["source"] = st.sidebar.radio(
        "Data Source",
        options=["both", "batch", "kafka"],
        format_func=lambda x: {
            "both": "All Sources",
            "batch": "Batch (CSV)",
            "kafka": "Kafka (Real-time)",
        }.get(x, x),
        index=0,
    )

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # Date range
    # ------------------------------------------------------------------

    st.sidebar.subheader("Date Range")

    default_start = datetime.now() - timedelta(days=7)
    default_end = datetime.now()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start", value=default_start)
    with col2:
        end_date = st.date_input("End", value=default_end)

    filters["start_date"] = datetime.combine(
        start_date, datetime.min.time()
    )
    filters["end_date"] = datetime.combine(
        end_date, datetime.max.time()
    )

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # Severity / Danger level
    # ------------------------------------------------------------------

    st.sidebar.subheader("Severity")

    filters["severities"] = st.sidebar.multiselect(
        "Violation Severity",
        options=config.SEVERITY_LEVELS,
        default=config.SEVERITY_LEVELS,
    )

    filters["danger_levels"] = st.sidebar.multiselect(
        "Alert Danger Level",
        options=config.DANGER_LEVELS,
        default=config.DANGER_LEVELS,
    )

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # Weighted score filter (CORE POLICY SIGNAL)
    # ------------------------------------------------------------------

    st.sidebar.subheader("Policy Score")

    filters["min_weighted_score"] = st.sidebar.slider(
        "Minimum Weighted Score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        help=(
            "Filters by the policy-weighted toxicity score "
            "(this is the main decision signal)"
        ),
    )

    st.sidebar.caption(
        "ℹ️ Weighted score combines multiple toxicity signals "
        "using policy-defined weights."
    )

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # Toxicity labels
    # ------------------------------------------------------------------

    st.sidebar.subheader("Toxicity Labels")

    labels = st.sidebar.multiselect(
        "Filter by Labels",
        options=config.TOXICITY_LABELS,
        default=[],
        help="Leave empty to include all labels",
    )

    filters["labels"] = labels if labels else None

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # Conversation search
    # ------------------------------------------------------------------

    filters["conversation_id"] = st.sidebar.text_input(
        "Search Conversation ID",
        value="",
        help="Partial match supported",
    ) or None

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # Time aggregation
    # ------------------------------------------------------------------

    filters["time_aggregation"] = st.sidebar.selectbox(
        "Time Aggregation",
        options=["H", "D"],
        format_func=lambda x: {"H": "Hourly", "D": "Daily"}[x],
        index=0,
    )

    st.sidebar.divider()

    # ------------------------------------------------------------------
    # Auto refresh
    # ------------------------------------------------------------------

    st.sidebar.subheader("Auto Refresh")

    filters["auto_refresh"] = st.sidebar.toggle(
        "Enable Auto Refresh",
        value=False,
    )

    if filters["auto_refresh"]:
        filters["refresh_interval"] = st.sidebar.selectbox(
            "Refresh Interval (seconds)",
            options=config.REFRESH_INTERVALS,
            index=2,
        )
    else:
        filters["refresh_interval"] = config.DEFAULT_REFRESH_INTERVAL

    if st.sidebar.button("Refresh Now"):
        st.cache_data.clear()
        st.rerun()

    return filters


# ------------------------------------------------------------------
# File info
# ------------------------------------------------------------------

def render_data_info(file_stats: Dict[str, Dict]):
    """
    Render data file information in sidebar
    """
    st.sidebar.divider()
    st.sidebar.subheader("Data Files")

    for filename, stats in file_stats.items():
        if not stats.get("exists"):
            st.sidebar.caption(f"**{filename}** — not found")
            continue

        modified = stats.get("modified")
        size_kb = stats.get("size", 0) / 1024

        st.sidebar.caption(f"**{filename}**")
        st.sidebar.caption(
            f"  Modified: {modified.strftime('%Y-%m-%d %H:%M:%S') if modified else 'unknown'}"
        )
        st.sidebar.caption(f"  Size: {size_kb:.1f} KB")
