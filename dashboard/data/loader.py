"""Data loading utilities for the dashboard"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import streamlit as st

from dashboard import config


class DataLoader:
    """Load and cache JSONL data files"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)

    # ------------------------------------------------------------------
    # Violations (MESSAGE-LEVEL)
    # ------------------------------------------------------------------

    @st.cache_data(ttl=5)
    def load_violations(_self, source: str = "both") -> pd.DataFrame:
        """
        Load violation events (message-level policy decisions).
        """
        files = []
        if source in ("batch", "both"):
            files.append(_self.output_dir / "violations.jsonl")
        if source in ("kafka", "both"):
            files.append(_self.output_dir / "kafka_violations.jsonl")

        records = []
        for file_path in files:
            if not file_path.exists():
                continue

            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # --------------------------------------------------------------
        # Core normalization
        # --------------------------------------------------------------

        # Timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")

        # 🔥 CORE POLICY SIGNAL
        if "weighted_score" in df.columns:
            df["weighted_score"] = df["weighted_score"].astype(float)

        # Severity as ordered category
        if "severity" in df.columns:
            df["severity"] = pd.Categorical(
                df["severity"],
                categories=["low", "medium", "high"],
                ordered=True,
            )

        # --------------------------------------------------------------
        # Explainability / diagnostics (optional, secondary)
        # --------------------------------------------------------------

        if "metadata" in df.columns:
            # Max raw Detoxify score (debug / charts)
            df["max_raw_score"] = df["metadata"].apply(
                lambda m: max(m.get("scores", {}).values())
                if isinstance(m, dict) and "scores" in m
                else None
            )

            # Number of labels triggered
            df["label_count"] = df["toxicity_labels"].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )

        return df

    # ------------------------------------------------------------------
    # Alerts (WINDOW-LEVEL)
    # ------------------------------------------------------------------

    @st.cache_data(ttl=5)
    def load_alerts(_self) -> pd.DataFrame:
        """
        Load alerts generated from sliding windows.
        """
        alerts_file = _self.output_dir / "alerts.jsonl"

        if not alerts_file.exists():
            return pd.DataFrame()

        records = []
        with open(alerts_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # --------------------------------------------------------------
        # Timestamp
        # --------------------------------------------------------------

        if "generated_at" in df.columns:
            df["timestamp"] = pd.to_datetime(df["generated_at"], format="ISO8601")
        elif "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")

        # --------------------------------------------------------------
        # Core alert signals
        # --------------------------------------------------------------

        if "window_score" in df.columns:
            df["window_score"] = df["window_score"].astype(float)

        if "danger_level" in df.columns:
            df["danger_level"] = pd.Categorical(
                df["danger_level"],
                categories=["low", "medium", "high"],
                ordered=True,
            )

        # Optional: alert strength buckets (visual aid)
        df["alert_strength"] = pd.cut(
            df["window_score"],
            bins=[0, 0.4, 0.8, float("inf")],
            labels=["weak", "strong", "critical"],
        )

        return df

    # ------------------------------------------------------------------
    # File stats (ops / debugging)
    # ------------------------------------------------------------------

    def get_file_stats(self) -> Dict[str, Dict]:
        stats = {}
        file_names = [
            "violations.jsonl",
            "kafka_violations.jsonl",
            "alerts.jsonl",
        ]

        for name in file_names:
            path = self.output_dir / name
            if path.exists():
                stat = path.stat()
                stats[name] = {
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "size": stat.st_size,
                    "exists": True,
                }
            else:
                stats[name] = {
                    "modified": None,
                    "size": 0,
                    "exists": False,
                }

        return stats

    def count_lines(self, filename: str) -> int:
        path = self.output_dir / filename
        if not path.exists():
            return 0

        with open(path, "r") as f:
            return sum(1 for line in f if line.strip())