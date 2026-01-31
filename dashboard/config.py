"""Dashboard configuration"""
import os

# File paths
VIOLATIONS_FILE = os.getenv("VIOLATIONS_FILE", "outputs/kafka_violations.jsonl")
ALERTS_FILE = os.getenv("ALERTS_FILE", "outputs/alerts.jsonl")
BATCH_VIOLATIONS_FILE = os.getenv("BATCH_VIOLATIONS_FILE", "outputs/violations.jsonl")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

# Dashboard settings
PAGE_TITLE = "LLM Guardrails Monitor"
PAGE_ICON = "🛡️"
LAYOUT = "wide"

# Refresh intervals (seconds)
DEFAULT_REFRESH_INTERVAL = 30
MIN_REFRESH_INTERVAL = 5
MAX_REFRESH_INTERVAL = 300

# Severity colors
SEVERITY_COLORS = {
    "low": "#FFA500",
    "medium": "#FF6347",
    "high": "#DC143C",
}

# Chart settings
CHART_HEIGHT = 400
TABLE_PAGE_SIZE = 20
DEFAULT_PAGE_SIZE = 20

# Toxicity labels (from Detoxify)
TOXICITY_LABELS = [
    "toxicity",
    "severe_toxicity",
    "insult",
    "threat",
    "identity_attack",
    "obscene",
    "sexual_explicit",
]

# Severity levels
SEVERITY_LEVELS = ["low", "medium", "high"]

# Danger levels (for alerts)
DANGER_LEVELS = ["low", "medium", "high"]
# Toxicity label colors for charts
TOXICITY_LABEL_COLORS = {
    "toxicity": "#FF6384",
    "severe_toxicity": "#DC143C",
    "insult": "#FF9F40",
    "threat": "#9966FF",
    "identity_attack": "#36A2EB",
    "obscene": "#FFCE56",
    "sexual_explicit": "#4BC0C0",
}


# Danger level colors for alerts
DANGER_COLORS = {
    "low": "#FFA500",
    "medium": "#FF6347",
    "high": "#DC143C",
}

# Text display settings
MAX_TEXT_LENGTH = 200
