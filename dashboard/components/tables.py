"""Data table components"""

import streamlit as st
import pandas as pd
from typing import Optional

from dashboard import config
from dashboard.data.processor import DataProcessor


# ------------------------------------------------------------------
# Violations Table
# ------------------------------------------------------------------

def render_violations_table(
    df: pd.DataFrame,
    page_size: int = 20,
    title: str = "Recent Violations"
):
    """
    Render interactive violations table with policy transparency
    """
    st.subheader(title)

    if df.empty:
        st.info("No violations to display")
        return

    display_df = df.copy()

    # Sort newest first
    if "timestamp" in display_df.columns:
        display_df = display_df.sort_values("timestamp", ascending=False)

    rows = []
    for _, row in display_df.iterrows():
        ts = (
            row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            if pd.notna(row.get("timestamp"))
            else ""
        )

        labels = row.get("toxicity_labels", [])
        if isinstance(labels, list):
            labels_str = ", ".join(labels[:3])
            if len(labels) > 3:
                labels_str += f" (+{len(labels) - 3})"
        else:
            labels_str = str(labels)

        rows.append({
            "Timestamp": ts,
            "Conversation": str(row.get("conversation_id", ""))[:15],
            "Text": DataProcessor.truncate_text(
                row.get("original_text", ""),
                config.MAX_TEXT_LENGTH
            ),
            "Severity": str(row.get("severity", "")).upper(),
            "Weighted Score": f"{row.get('weighted_score', 0.0):.3f}",
            "Labels": labels_str,
        })

    table_df = pd.DataFrame(rows)

    _render_paginated_table(
        table_df,
        page_size=page_size,
        severity_column="Severity",
        color_map=config.SEVERITY_COLORS,
        key_prefix="violations"
    )


# ------------------------------------------------------------------
# Alerts Table
# ------------------------------------------------------------------

def render_alerts_table(
    df: pd.DataFrame,
    page_size: int = 15,
    title: str = "Recent Alerts"
):
    """
    Render interactive alerts table with full policy explainability
    """
    st.subheader(title)

    if df.empty:
        st.info("No alerts to display")
        return

    display_df = df.copy()

    if "timestamp" in display_df.columns:
        display_df = display_df.sort_values("timestamp", ascending=False)

    rows = []
    for _, row in display_df.iterrows():
        ts = (
            row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            if pd.notna(row.get("timestamp"))
            else ""
        )

        summary = row.get("summary", {})
        labels = summary.get("labels", []) if isinstance(summary, dict) else []
        labels_str = ", ".join(labels[:3]) if labels else ""

        rows.append({
            "Timestamp": ts,
            "Alert ID": str(row.get("alert_id", ""))[:12],
            "Conversation": str(row.get("conversation_id", ""))[:15],
            "Danger Level": str(row.get("danger_level", "")).upper(),
            "Window Score": f"{row.get('window_score', 0.0):.3f}",
            "Violations": row.get("violation_count", 0),
            "Window": f"{row.get('window_size_minutes', 5)} min",
            "Labels": labels_str,
        })

    table_df = pd.DataFrame(rows)

    _render_paginated_table(
        table_df,
        page_size=page_size,
        severity_column="Danger Level",
        color_map=config.DANGER_COLORS,
        key_prefix="alerts"
    )


# ------------------------------------------------------------------
# Shared pagination + styling
# ------------------------------------------------------------------

def _render_paginated_table(
    df: pd.DataFrame,
    page_size: int,
    severity_column: str,
    color_map: dict,
    key_prefix: str
):
    total_rows = len(df)
    total_pages = max(1, (total_rows - 1) // page_size + 1)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        page = st.selectbox(
            "Page",
            options=range(1, total_pages + 1),
            format_func=lambda x: f"Page {x} of {total_pages}",
            key=f"{key_prefix}_page"
        )

    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    def style_severity(val):
        val = str(val).lower()
        if val in color_map:
            return f"background-color: {color_map[val]}; color: white"
        return ""

    styled = page_df.style.applymap(
        style_severity,
        subset=[severity_column]
    )

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Showing {start + 1}-{min(end, total_rows)} of {total_rows}"
    )
