from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class Conversation:
    conversation_id: str
    text: str
    timestamp: datetime
    speaker: str  # 'user' or 'agent'

    @classmethod
    def from_dict(cls, data: dict):
        if "conversation_id" not in data or "text" not in data:
            raise ValueError(f"Invalid conversation payload: {data}")

        ts = data.get("timestamp")

        if isinstance(ts, datetime):
            timestamp = ts
        elif isinstance(ts, str):
            try:
                # Handles ISO + optional Z
                timestamp = datetime.fromisoformat(
                    ts.replace("Z", "+00:00")
                )
            except Exception as e:
                raise ValueError(
                    f"Invalid timestamp format: {ts}"
                ) from e
        else:
            raise ValueError(f"Missing or invalid timestamp: {ts}")

        # Ensure UTC
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        return cls(
            conversation_id=data["conversation_id"],
            text=data["text"],
            timestamp=timestamp,
            speaker=data.get("speaker", "user"),
        )
