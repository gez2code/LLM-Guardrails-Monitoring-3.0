from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict
from enum import Enum
import numpy as np


def convert_numpy_types(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(convert_numpy_types(v) for v in obj)
    return obj


class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Violation:
    # identity
    conversation_id: str
    original_timestamp: datetime
    ingested_at: datetime
    original_text: str

    # 🔥 CORE SIGNAL
    weighted_score: float

    # derived classification
    severity: SeverityLevel
    toxicity_labels: List[str]

    # optional / audit
    metadata: Dict

    def to_dict(self):
        data = asdict(self)

        data["original_timestamp"] = self.original_timestamp.isoformat()
        data["ingested_at"] = self.ingested_at.isoformat()
        data["severity"] = self.severity.value

        # 🔥 FIX: convert ALL numpy types
        data = convert_numpy_types(data)

        return data


