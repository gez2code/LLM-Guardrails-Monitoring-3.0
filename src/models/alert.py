from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, Optional
from enum import Enum


class DangerLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Alert:
    """
    Alert generated when policy thresholds are exceeded
    within a sliding window.

    timestamp     = event-time (derived from violations)
    generated_at  = processing-time (alert emission)
    """

    alert_id: str
    conversation_id: str

    danger_level: DangerLevel

    # 🔥 NEW: aggregated policy signal
    window_score: float

    violation_count: int
    window_size_minutes: int

    # ⏱️ EVENT TIME (earliest violation in window)
    timestamp: datetime

    # ⏱️ PROCESSING TIME (Kafka / consumer time)
    generated_at: Optional[datetime] = None

    summary: Dict = field(default_factory=dict)

    def __post_init__(self):
        # Ensure processing time always exists
        if self.generated_at is None:
            self.generated_at = datetime.now(timezone.utc)

    def to_dict(self):
        data = asdict(self)

        data["timestamp"] = self.timestamp.isoformat()
        data["generated_at"] = self.generated_at.isoformat()
        data["danger_level"] = self.danger_level.value

        return data
