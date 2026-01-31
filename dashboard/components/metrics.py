"""KPI metric cards component (policy-aligned)"""

import streamlit as st
import pandas as pd
from typing import Optional


# ==========================================================
# TOP-LEVEL KPIs
# ==========================================================

def render_metric_cards(
    violations_df: pd.DataFrame,
    alerts_df: pd.DataFrame,
):
    """
    Render top-level KPI metric cards.
    Focus: policy effectiveness & signal strength.
    """

    col1, col2, col3, col4, col5 = st.columns(5)

    total_violations = len(violations_df)
    total_alerts = len(alerts_df)

    # ------------------------------------------------------
    # Violation Rate
    # ------------------------------------------------------
    violation_rate = None
    if not violations_df.empty:
        violation_rate = total_violations

    with col1:
        st.metric(
            label="Violations",
            value=total_violations,
        )

    # ------------------------------------------------------
    # Alerts
    # ------------------------------------------------------
    with col2:
        st.metric(
            label="Alerts",
            value=total_alerts,
        )

    # ------------------------------------------------------
    # Escalation Rate
    # ------------------------------------------------------
    escalation_rate = 0.0
    if total_violations > 0:
        escalation_rate = total_alerts / total_violations

    with col3:
        st.metric(
            label="Escalation Rate",
            value=f"{escalation_rate:.1%}",
        )

    # ------------------------------------------------------
    # Mean weighted_score (message-level)
    # ------------------------------------------------------
    mean_weighted = 0.0
    if not violations_df.empty and "weighted_score" in violations_df.columns:
        mean_weighted = violations_df["weighted_score"].mean()

    with col4:
        st.metric(
            label="Mean Weighted Score",
            value=f"{mean_weighted:.3f}",
        )

    # ------------------------------------------------------
    # Mean window_score (alert-level)
    # ------------------------------------------------------
    mean_window = 0.0
    if not alerts_df.empty and "window_score" in alerts_df.columns:
        mean_window = alerts_df["window_score"].mean()

    with col5:
        st.metric(
            label="Mean Window Score",
            value=f"{mean_window:.3f}",
        )


# ==========================================================
# SEVERITY / DANGER BREAKDOWN
# ==========================================================

def render_severity_metrics(violations_df: pd.DataFrame):
    """
    Render severity distribution metrics (message-level).
    """
    col1, col2, col3 = st.columns(3)

    high = len(violations_df[violations_df["severity"] == "high"]) if "severity" in violations_df.columns else 0
    medium = len(violations_df[violations_df["severity"] == "medium"]) if "severity" in violations_df.columns else 0
    low = len(violations_df[violations_df["severity"] == "low"]) if "severity" in violations_df.columns else 0

    with col1:
        st.metric("High Severity", high, delta_color="inverse")

    with col2:
        st.metric("Medium Severity", medium)

    with col3:
        st.metric("Low Severity", low)


def render_alert_metrics(alerts_df: pd.DataFrame):
    """
    Render alert danger-level metrics (window-level).
    """
    col1, col2, col3 = st.columns(3)

    high = len(alerts_df[alerts_df["danger_level"] == "high"]) if "danger_level" in alerts_df.columns else 0
    medium = len(alerts_df[alerts_df["danger_level"] == "medium"]) if "danger_level" in alerts_df.columns else 0
    low = len(alerts_df[alerts_df["danger_level"] == "low"]) if "danger_level" in alerts_df.columns else 0

    with col1:
        st.metric("High Danger Alerts", high, delta_color="inverse")

    with col2:
        st.metric("Medium Danger Alerts", medium)

    with col3:
        st.metric("Low Danger Alerts", low)
