from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from collections import defaultdict
from loguru import logger


class SlidingWindowTracker:
    """
    Track violations per conversation in a sliding time window.

    Window semantics:
    - Windowing is based on INGESTION TIME (ingested_at)
    - Event time (original_timestamp) is NOT used for window logic
    """

    def __init__(self, window_size_seconds: int = 300):
        self.window_size = window_size_seconds

        # {
        #   conversation_id: [(ingested_at_utc, violation_dict), ...]
        # }
        self.windows: Dict[str, List[Tuple[datetime, dict]]] = defaultdict(list)

        logger.info(
            f"SlidingWindowTracker initialized (window={window_size_seconds}s)"
        )

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def add_violation(self, violation: dict) -> int:
        """
        Add a violation to the sliding window.

        Uses:
        - violation['ingested_at']  ✅ primary
        - violation['timestamp']    ⚠️ fallback (legacy only)
        """
        conv_id = violation["conversation_id"]

        timestamp = self._parse_timestamp(
            violation.get("ingested_at")
            or violation.get("timestamp")
        )

        score = float(violation.get("weighted_score", 0.0))

        logger.debug(
            f"[Window:add] conversation={conv_id} "
            f"ingested_at={timestamp.isoformat()} "
            f"score={score:.4f}"
        )

        self.windows[conv_id].append((timestamp, violation))

        # Remove expired entries
        self._clean_expired(conv_id, timestamp)

        count = len(self.windows.get(conv_id, []))
        window_score = self.get_window_score(conv_id)

        logger.debug(
            f"[Window:state] conversation={conv_id} "
            f"count={count} window_score={window_score:.4f}"
        )

        return count

    def get_violations(self, conv_id: str) -> List[dict]:
        return [v for _, v in self.windows.get(conv_id, [])]

    def get_window_count(self, conv_id: str) -> int:
        return len(self.windows.get(conv_id, []))

    def get_window_score(self, conv_id: str) -> float:
        """
        Sum CORE weighted_score across window.
        """
        total = 0.0
        for _, violation in self.windows.get(conv_id, []):
            total += float(violation.get("weighted_score", 0.0))
        return total

    # ------------------------------------------------------------------
    # Alert / Flush Logic
    # ------------------------------------------------------------------

    def should_flush(self, conv_id: str, now: datetime) -> bool:
        """
        Decide whether the current window should be flushed.

        Flush conditions:
        - window_score exceeds hard limit
        - window duration exceeded (based on ingested_at)
        """
        if conv_id not in self.windows or not self.windows[conv_id]:
            logger.debug(
                f"[Window:flush] conversation={conv_id} → no active window"
            )
            return False

        now = self._normalize_to_utc(now)

        window_score = self.get_window_score(conv_id)
        count = self.get_window_count(conv_id)

        # 🔥 Score-based early flush
        if window_score >= 1.0:
            logger.debug(
                f"[Window:flush] conversation={conv_id} "
                f"reason=score window_score={window_score:.4f} "
                f"count={count}"
            )
            return True

        # ⏱️ Time-based flush (INGESTION TIME)
        oldest_timestamp, _ = self.windows[conv_id][0]
        oldest_timestamp = self._normalize_to_utc(oldest_timestamp)

        elapsed = (now - oldest_timestamp).total_seconds()

        logger.debug(
            f"[Window:flush-check] conversation={conv_id} "
            f"elapsed={elapsed:.1f}s window={self.window_size}s "
            f"window_score={window_score:.4f} count={count}"
        )

        if elapsed >= self.window_size:
            logger.debug(
                f"[Window:flush] conversation={conv_id} "
                f"reason=time elapsed={elapsed:.1f}s"
            )
            return True

        return False

    def clear_window(self, conv_id: str):
        count = len(self.windows.get(conv_id, []))
        score = self.get_window_score(conv_id)

        self.windows.pop(conv_id, None)

        logger.debug(
            f"[Window:clear] conversation={conv_id} "
            f"cleared_count={count} cleared_score={score:.4f}"
        )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _clean_expired(self, conv_id: str, now: datetime):
        cutoff = now - timedelta(seconds=self.window_size)
        before = len(self.windows[conv_id])

        self.windows[conv_id] = [
            (ts, v)
            for ts, v in self.windows[conv_id]
            if ts >= cutoff
        ]

        after = len(self.windows[conv_id])

        if after < before:
            logger.debug(
                f"[Window:expire] conversation={conv_id} "
                f"expired={before - after} remaining={after}"
            )

        if not self.windows[conv_id]:
            del self.windows[conv_id]
            logger.debug(
                f"[Window:expired] conversation={conv_id} window empty"
            )

    @staticmethod
    def _parse_timestamp(ts: str | datetime) -> datetime:
        if isinstance(ts, datetime):
            return SlidingWindowTracker._normalize_to_utc(ts)

        parsed = datetime.fromisoformat(ts)
        return SlidingWindowTracker._normalize_to_utc(parsed)

    @staticmethod
    def _normalize_to_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
