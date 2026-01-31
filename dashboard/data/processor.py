"""Data processing and transformation utilities"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

from dashboard import config


class DataProcessor:
    """
    Transform and aggregate data for visualization (policy-aware).

    Design principles:
    - ingestion_time is the SINGLE source of truth for time
    - all public methods are UTC-safe and idempotent
    - no hidden assumptions about call order
    """

    # 🔥 SINGLE SOURCE OF TRUTH FOR TIME AXIS
    TIME_COLUMN = "ingested_at"

    # ------------------------------------------------------------------
    # Core filtering
    # ------------------------------------------------------------------

    @staticmethod
    def filter_data(
        df: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severities: Optional[List[str]] = None,
        danger_levels: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        min_weighted_score: float = 0.0,
        **_,
    ) -> pd.DataFrame:
        """
        Apply policy-aware filters to violations or alerts DataFrame.
        Uses ingestion time as the canonical time axis.
        """
        if df.empty:
            return df

        filtered = df.copy()

        # ------------------------------------------------------------------
        # ⏱️ Time range (INGESTION TIME, UTC-safe)
        # ------------------------------------------------------------------

        if DataProcessor.TIME_COLUMN in filtered.columns:
            filtered[DataProcessor.TIME_COLUMN] = pd.to_datetime(
                filtered[DataProcessor.TIME_COLUMN],
                utc=True,
                errors="coerce",
            )

            if start_date:
                start = pd.to_datetime(start_date, utc=True)
                filtered = filtered[
                    filtered[DataProcessor.TIME_COLUMN] >= start
                ]

            if end_date:
                end = pd.to_datetime(end_date, utc=True)
                filtered = filtered[
                    filtered[DataProcessor.TIME_COLUMN] <= end
                ]

        # ------------------------------------------------------------------
        # Severity (violations)
        # ------------------------------------------------------------------

        if severities and "severity" in filtered.columns:
            filtered = filtered[
                filtered["severity"].isin(severities)
            ]

        # ------------------------------------------------------------------
        # Danger level (alerts)
        # ------------------------------------------------------------------

        if danger_levels and "danger_level" in filtered.columns:
            filtered = filtered[
                filtered["danger_level"].isin(danger_levels)
            ]

        # ------------------------------------------------------------------
        # 🔥 Weighted policy score (CORE SIGNAL)
        # ------------------------------------------------------------------

        if min_weighted_score > 0 and "weighted_score" in filtered.columns:
            filtered = filtered[
                filtered["weighted_score"] >= min_weighted_score
            ]

        # ------------------------------------------------------------------
        # Toxicity labels (explanatory only)
        # ------------------------------------------------------------------

        if labels and "toxicity_labels" in filtered.columns:
            filtered = filtered[
                filtered["toxicity_labels"].apply(
                    lambda xs: (
                        isinstance(xs, list)
                        and any(label in xs for label in labels)
                    )
                )
            ]

        # ------------------------------------------------------------------
        # Conversation search
        # ------------------------------------------------------------------

        if conversation_id and "conversation_id" in filtered.columns:
            filtered = filtered[
                filtered["conversation_id"]
                .astype(str)
                .str.contains(conversation_id, case=False, na=False)
            ]

        return filtered

    # ------------------------------------------------------------------
    # Aggregations
    # ------------------------------------------------------------------

    @staticmethod
    def aggregate_by_time(
        df: pd.DataFrame,
        freq: str = "H",
        value_column: str = "severity",
    ) -> pd.DataFrame:
        """
        Aggregate events by time bucket using ingestion time.
        Safe to call independently of filter_data().
        """
        if df.empty or DataProcessor.TIME_COLUMN not in df.columns:
            return pd.DataFrame(columns=["period", value_column, "count"])

        df = df.copy()

        # 🔒 Defensive datetime normalization
        df[DataProcessor.TIME_COLUMN] = pd.to_datetime(
            df[DataProcessor.TIME_COLUMN],
            utc=True,
            errors="coerce",
        )

        df["period"] = df[DataProcessor.TIME_COLUMN].dt.floor(freq)

        if value_column in df.columns:
            return (
                df.groupby(["period", value_column])
                .size()
                .reset_index(name="count")
            )

        return (
            df.groupby("period")
            .size()
            .reset_index(name="count")
        )

    # ------------------------------------------------------------------
    # Distributions
    # ------------------------------------------------------------------

    @staticmethod
    def get_label_counts(df: pd.DataFrame) -> Dict[str, int]:
        counts = {label: 0 for label in config.TOXICITY_LABELS}

        if df.empty or "toxicity_labels" not in df.columns:
            return counts

        for labels in df["toxicity_labels"]:
            if isinstance(labels, list):
                for label in labels:
                    if label in counts:
                        counts[label] += 1

        return counts

    @staticmethod
    def get_severity_distribution(df: pd.DataFrame) -> Dict[str, int]:
        distribution = {level: 0 for level in config.SEVERITY_LEVELS}

        if df.empty or "severity" not in df.columns:
            return distribution

        distribution.update(df["severity"].value_counts().to_dict())
        return distribution

    @staticmethod
    def get_danger_distribution(df: pd.DataFrame) -> Dict[str, int]:
        distribution = {level: 0 for level in config.DANGER_LEVELS}

        if df.empty or "danger_level" not in df.columns:
            return distribution

        distribution.update(df["danger_level"].value_counts().to_dict())
        return distribution

    # ------------------------------------------------------------------
    # Score extraction (for heatmaps only)
    # ------------------------------------------------------------------

    @staticmethod
    def extract_scores(df: pd.DataFrame) -> pd.DataFrame:
        """
        Flatten raw Detoxify scores for heatmap visualization only.
        """
        if df.empty or "metadata" not in df.columns:
            return pd.DataFrame()

        records = []

        for _, row in df.iterrows():
            scores = (
                row.get("metadata", {}).get("scores", {})
                if isinstance(row.get("metadata"), dict)
                else {}
            )

            record = {
                "conversation_id": row.get("conversation_id", ""),
                "timestamp": row.get(DataProcessor.TIME_COLUMN),
                "severity": row.get("severity", ""),
            }

            for label in config.TOXICITY_LABELS:
                record[label] = scores.get(label, 0.0)

            records.append(record)

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_top_score(metadata: dict) -> float:
        """Max raw Detoxify score (table-only helper)."""
        if not isinstance(metadata, dict):
            return 0.0
        scores = metadata.get("scores", {})
        return max(scores.values()) if scores else 0.0

    @staticmethod
    def truncate_text(text: str, max_length: int = 80) -> str:
        if not isinstance(text, str):
            return ""
        return text if len(text) <= max_length else text[:max_length] + "..."