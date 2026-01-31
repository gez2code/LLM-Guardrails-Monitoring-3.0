"""Chart components using Plotly"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard import config
from dashboard.data.processor import DataProcessor


# ------------------------------------------------------------
# Time series
# ------------------------------------------------------------

def render_time_series(
    df: pd.DataFrame,
    title: str,
    color_column: str,
    freq: str = "H",
):
    if df.empty:
        st.info("No data available")
        return

    agg = DataProcessor.aggregate_by_time(
        df,
        freq=freq,
        value_column=color_column,
    )

    if agg.empty:
        st.info("No data available")
        return

    color_map = (
        config.SEVERITY_COLORS
        if color_column == "severity"
        else config.DANGER_COLORS
        if color_column == "danger_level"
        else None
    )

    fig = px.line(
        agg,
        x="period",
        y="count",
        color=color_column if color_column in agg.columns else None,
        color_discrete_map=color_map,
        markers=True,
        title=title,
    )

    fig.update_layout(
        height=config.CHART_HEIGHT,
        xaxis_title="Time",
        yaxis_title="Count",
    )

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# Label distribution
# ------------------------------------------------------------

def render_label_distribution(df: pd.DataFrame):
    if df.empty:
        st.info("No data available")
        return

    counts = DataProcessor.get_label_counts(df)
    data = (
        pd.DataFrame(
            [{"label": k, "count": v} for k, v in counts.items() if v > 0]
        )
        .sort_values("count")
    )

    if data.empty:
        st.info("No label data available")
        return

    fig = px.bar(
        data,
        x="count",
        y="label",
        orientation="h",
        color="label",
        color_discrete_map=config.TOXICITY_LABEL_COLORS,
        title="Toxicity Label Distribution",
    )

    fig.update_layout(
        height=config.CHART_HEIGHT,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# Severity pie
# ------------------------------------------------------------

def render_severity_pie(df: pd.DataFrame):
    if df.empty:
        st.info("No data available")
        return

    dist = DataProcessor.get_severity_distribution(df)
    data = pd.DataFrame(
        [{"severity": k, "count": v} for k, v in dist.items() if v > 0]
    )

    if data.empty:
        st.info("No severity data")
        return

    fig = px.pie(
        data,
        names="severity",
        values="count",
        hole=0.4,
        color="severity",
        color_discrete_map=config.SEVERITY_COLORS,
        title="Severity Distribution",
    )

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# Danger pie (alerts)
# ------------------------------------------------------------

def render_danger_pie(df: pd.DataFrame):
    if df.empty:
        st.info("No alerts available")
        return

    dist = DataProcessor.get_danger_distribution(df)
    data = pd.DataFrame(
        [{"danger_level": k, "count": v} for k, v in dist.items() if v > 0]
    )

    if data.empty:
        st.info("No danger data")
        return

    fig = px.pie(
        data,
        names="danger_level",
        values="count",
        hole=0.4,
        color="danger_level",
        color_discrete_map=config.DANGER_COLORS,
        title="Alert Danger Levels",
    )

    st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------
# Score heatmap
# ------------------------------------------------------------

def render_score_heatmap(df: pd.DataFrame):
    if df.empty:
        st.info("No data available")
        return

    scores = DataProcessor.extract_scores(df).tail(20)
    if scores.empty:
        st.info("No score data available")
        return

    labels = config.TOXICITY_LABELS

    fig = go.Figure(
        data=go.Heatmap(
            z=scores[labels].values,
            x=labels,
            y=scores["conversation_id"].str[:12],
            colorscale="RdYlGn_r",
            zmin=0,
            zmax=1,
        )
    )

    fig.update_layout(
        title="Toxicity Score Heatmap",
        height=max(400, len(scores) * 25),
    )

    st.plotly_chart(fig, use_container_width=True)
