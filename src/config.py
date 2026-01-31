"""Dashboard configuration settings"""

from dataclasses import dataclass, field
from typing import Dict, List
from pathlib import Path
import os


@dataclass
class DashboardConfig:
    """Configuration for Streamlit dashboard"""

    # ------------------------------------------------------------------
    # Data paths
    # ------------------------------------------------------------------
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")

    # ------------------------------------------------------------------
    # Page settings
    # ------------------------------------------------------------------
    PAGE_TITLE: str = "LLM Monitoring Dashboard"
    PAGE_ICON: str = ":shield:"
    LAYOUT: str = "wide"

    # ------------------------------------------------------------------
    # Refresh settings
    # ------------------------------------------------------------------
    DEFAULT_REFRESH_INTERVAL: int = 30
    REFRESH_INTERVALS: List[int] = field(
        default_factory=lambda: [5, 10, 30, 60, 120, 300]
    )

    # ------------------------------------------------------------------
    # Table settings
    # ------------------------------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_TEXT_LENGTH: int = 80

    # ------------------------------------------------------------------
    # Chart settings
    # ------------------------------------------------------------------
    CHART_HEIGHT: int = 420

    # ------------------------------------------------------------------
    # Toxicity labels (SYNCED WITH Detoxify + GuardrailProcessor)
    # ------------------------------------------------------------------
    TOXICITY_LABELS: List[str] = field(default_factory=lambda: [
        "toxicity",
        "severe_toxicity",
        "obscene",
        "threat",
        "insult",
        "identity_attack",
        "profanity",
        "sexual_explicit",
    ])

    # ------------------------------------------------------------------
    # Severity levels (message-level)
    # ------------------------------------------------------------------
    SEVERITY_LEVELS: List[str] = field(
        default_factory=lambda: ["low", "medium", "high"]
    )

    # ------------------------------------------------------------------
    # Danger levels (window / alert-level)
    # ------------------------------------------------------------------
    DANGER_LEVELS: List[str] = field(
        default_factory=lambda: ["low", "medium", "high"]
    )

    # ------------------------------------------------------------------
    # Color schemes
    # ------------------------------------------------------------------
    SEVERITY_COLORS: Dict[str, str] = field(default_factory=lambda: {
        "low": "#4CAF50",      # Green
        "medium": "#FF9800",   # Orange
        "high": "#F44336",     # Red
    })

    DANGER_COLORS: Dict[str, str] = field(default_factory=lambda: {
        "low": "#4CAF50",
        "medium": "#FF9800",
        "high": "#F44336",
    })

    TOXICITY_LABEL_COLORS: Dict[str, str] = field(default_factory=lambda: {
        "toxicity": "#E91E63",
        "severe_toxicity": "#9C27B0",
        "obscene": "#673AB7",
        "threat": "#F44336",
        "insult": "#FF5722",
        "identity_attack": "#795548",
        "profanity": "#607D8B",
        "sexual_explicit": "#3F51B5",
    })

    # ------------------------------------------------------------------
    @property
    def output_path(self) -> Path:
        return Path(self.OUTPUT_DIR)


@dataclass
class KafkaInputConfig:
    """Configuration for Kafka input processor"""
    BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    INPUT_TOPIC: str = os.getenv("KAFKA_INPUT_TOPIC", "llm.conversations")
    OUTPUT_TOPIC: str = os.getenv("KAFKA_OUTPUT_TOPIC", "guardrail.violations")
    CONSUMER_GROUP: str = os.getenv("KAFKA_INPUT_CONSUMER_GROUP", "guardrail-input-processor-group")
    OUTPUT_FILE: str = os.getenv("KAFKA_INPUT_OUTPUT_FILE", "outputs/kafka_violations.jsonl")


@dataclass
class AlertConfig:
    """Configuration for alert consumer"""
    BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    TOPIC: str = os.getenv("KAFKA_TOPIC", "guardrail.violations")
    CONSUMER_GROUP: str = os.getenv("ALERT_CONSUMER_GROUP", "alert-consumer-group")
    WINDOW_SIZE_SECONDS: int = int(os.getenv("ALERT_WINDOW_SIZE_SECONDS", "300"))
    LOW_THRESHOLD: float = float(os.getenv("ALERT_LOW_THRESHOLD", "0.15"))
    MEDIUM_THRESHOLD: float = float(os.getenv("ALERT_MEDIUM_THRESHOLD", "0.40"))
    HIGH_THRESHOLD: float = float(os.getenv("ALERT_HIGH_THRESHOLD", "0.80"))
    OUTPUT_FILE: str = os.getenv("ALERT_OUTPUT_FILE", "outputs/alerts.jsonl")


# Global config instance
config = DashboardConfig()