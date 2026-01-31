from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger

from src.models.alert import Alert, DangerLevel


class AlertGenerator:
    """
    Generate alerts from windowed violations.

    Time semantics:
    - Window logic is based on INGESTION TIME
    - Alert.timestamp = earliest ingested_at in window
    - Event/original timestamps are NOT used for alert triggering
    """

    def __init__(
        self,
        window_size_minutes: int = 5,
        low_threshold: float = 0.15,
        medium_threshold: float = 0.40,
        high_threshold: float = 0.8,
    ):
        self.window_size_minutes = window_size_minutes

        self.thresholds = {
            DangerLevel.LOW: low_threshold,
            DangerLevel.MEDIUM: medium_threshold,
            DangerLevel.HIGH: high_threshold,
        }

        logger.info(
            "AlertGenerator initialized | "
            f"window={window_size_minutes}m "
            f"thresholds=low:{low_threshold} "
            f"medium:{medium_threshold} "
            f"high:{high_threshold}"
        )

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def generate_alert(
        self,
        conversation_id: str,
        violations: List[dict],
    ) -> Optional[Alert]:

        if not violations:
            logger.debug(
                f"[AlertGen] conversation={conversation_id} → no violations"
            )
            return None

        window_score = self._compute_window_score(violations)

        logger.debug(
            f"[AlertGen] conversation={conversation_id} "
            f"violations={len(violations)} "
            f"window_score={window_score:.4f}"
        )

        danger_level = self._classify_danger_level(window_score)

        if danger_level is None:
            logger.debug(
                f"[AlertGen] conversation={conversation_id} "
                f"NO ALERT (score {window_score:.4f} "
                f"< low_threshold {self.thresholds[DangerLevel.LOW]})"
            )
            return None

        # ⏱️ ALERT TIME = earliest INGESTION time in window
        earliest_ingested_at = min(
            self._parse_timestamp(
                v.get("ingested_at") or v.get("timestamp")
            )
            for v in violations
        )

        alert_id = (
            f"alert_{conversation_id}_"
            f"{int(datetime.now(timezone.utc).timestamp())}"
        )

        alert = Alert(
            alert_id=alert_id,
            conversation_id=conversation_id,
            danger_level=danger_level,
            window_score=window_score,
            violation_count=len(violations),
            window_size_minutes=self.window_size_minutes,

            # 🔥 canonical alert time
            timestamp=earliest_ingested_at,

            # audit metadata
            generated_at=datetime.now(timezone.utc),
            summary=self._build_summary(violations),
        )

        logger.warning(
            f"[ALERT] level={danger_level.value.upper()} "
            f"conversation={conversation_id} "
            f"window_score={window_score:.4f} "
            f"count={len(violations)} "
            f"threshold={self.thresholds[danger_level]}"
        )

        return alert

    # ------------------------------------------------------------------
    # Policy logic
    # ------------------------------------------------------------------

    def _compute_window_score(self, violations: List[dict]) -> float:
        """
        Sum CORE weighted_score across window.
        """
        scores = [
            float(v.get("weighted_score", 0.0))
            for v in violations
        ]

        total = sum(scores)

        logger.debug(
            f"[AlertGen:score] scores={['%.3f' % s for s in scores]} "
            f"sum={total:.4f}"
        )

        return total

    def _classify_danger_level(
        self, window_score: float
    ) -> Optional[DangerLevel]:

        if window_score >= self.thresholds[DangerLevel.HIGH]:
            logger.debug(
                f"[AlertGen:classify] score={window_score:.4f} → HIGH"
            )
            return DangerLevel.HIGH

        if window_score >= self.thresholds[DangerLevel.MEDIUM]:
            logger.debug(
                f"[AlertGen:classify] score={window_score:.4f} → MEDIUM"
            )
            return DangerLevel.MEDIUM

        if window_score >= self.thresholds[DangerLevel.LOW]:
            logger.debug(
                f"[AlertGen:classify] score={window_score:.4f} → LOW"
            )
            return DangerLevel.LOW

        logger.debug(
            f"[AlertGen:classify] score={window_score:.4f} → BELOW LOW"
        )
        return None

    def _build_summary(self, violations: List[dict]) -> dict:
        labels = {
            label
            for v in violations
            for label in v.get("toxicity_labels", [])
        }

        return {
            "total_violations": len(violations),
            "labels": sorted(labels),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(ts) -> datetime:
        if isinstance(ts, datetime):
            return ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(
                tzinfo=timezone.utc
            )

        parsed = datetime.fromisoformat(ts)
        return (
            parsed.astimezone(timezone.utc)
            if parsed.tzinfo
            else parsed.replace(tzinfo=timezone.utc)
        )
