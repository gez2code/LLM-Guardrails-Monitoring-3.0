import guardrails as gd
from guardrails.hub import ToxicLanguage
from detoxify import Detoxify
from typing import Optional, Dict
from loguru import logger
from datetime import datetime, timezone

from src.models.conversation import Conversation
from src.models.violation import Violation, SeverityLevel


class GuardrailProcessor:
    """
    GuardrailProcessor responsibilities (clean separation):

    1. Detoxify        → continuous toxicity signal (per label)
    2. Policy Engine   → weighted max score
    3. Violation Gate  → binary decision
    4. Guardrails      → enforcement ONLY for high severity
    """

    # ---------------------------------------------------------
    # Policy configuration
    # ---------------------------------------------------------

    # Impact weights (NOT probabilities)
    WEIGHTS: Dict[str, float] = {
        "toxicity": 1.0,
        "insult": 1.0,
        "profanity": 0.8,
        "obscene": 1.0,
        "sexual_explicit": 1.2,
        "threat": 2.0,
        "identity_attack": 2.0,
        "severe_toxicity": 2.5,
    }

    # Binary violation gate (entry into monitoring / alerts)
    VIOLATION_THRESHOLD = 0.10

    # Label reporting threshold (dashboard clarity)
    LABEL_THRESHOLD = 0.10

    # Severity buckets (policy-level semantics)
    BUCKET_THRESHOLDS = {
        SeverityLevel.LOW: 0.30,
        SeverityLevel.MEDIUM: 0.60,
        SeverityLevel.HIGH: 0.85,
    }

    def __init__(self, guardrail_threshold: float = 0.7):
        # Guardrails = enforcement gate ONLY (not detector)
        self.guard = gd.Guard().use(
            ToxicLanguage(
                threshold=guardrail_threshold,
                validation_method="sentence",
                on_fail="exception",
            )
        )

        self.detoxify_model = Detoxify("original")

        logger.info(
            "GuardrailProcessor initialized | "
            f"violation_threshold={self.VIOLATION_THRESHOLD}, "
            f"guardrail_threshold={guardrail_threshold}"
        )

    # ---------------------------------------------------------
    # Main entry point
    # ---------------------------------------------------------

    def process_conversation(
        self, conversation: Conversation
    ) -> Optional[Violation]:

        # 1️⃣ Detoxify signal (0–1 per label)
        scores = self.detoxify_model.predict(conversation.text)

        # 2️⃣ Core policy signal (weighted MAX)
        weighted_score = self._compute_weighted_max_score(scores)

        # 3️⃣ Binary violation gate
        if weighted_score < self.VIOLATION_THRESHOLD:
            return None

        # 4️⃣ Severity classification
        severity = self._bucket_from_score(weighted_score)

        # 5️⃣ Guardrails enforcement ONLY for HIGH
        if severity == SeverityLevel.HIGH:
            try:
                self.guard.validate(conversation.text)
            except Exception:
                logger.warning(
                    f"Guardrail blocked conversation={conversation.conversation_id}"
                )

        # Report only meaningful labels
        toxic_labels = [
            label
            for label, score in scores.items()
            if score >= self.LABEL_THRESHOLD
        ]

        return Violation(
            conversation_id=conversation.conversation_id,
            original_timestamp=conversation.timestamp,
            ingested_at=datetime.now(timezone.utc),
            original_text=conversation.text,

            # 🔥 CORE SIGNAL
            weighted_score=float(weighted_score),

            severity=severity,
            toxicity_labels=toxic_labels,

            metadata={
                "scores": scores,
                "policy": "weighted_max",
                "violation_threshold": self.VIOLATION_THRESHOLD,
                "bucket_thresholds": {
                    k.value: v for k, v in self.BUCKET_THRESHOLDS.items()
                },
            },
        )

    # ---------------------------------------------------------
    # Policy logic
    # ---------------------------------------------------------

    def _compute_weighted_max_score(self, scores: Dict[str, float]) -> float:
        """
        Compute weighted max toxicity score.

        Rationale:
        - One severe signal is sufficient
        - Avoids dilution from benign labels
        """
        return max(
            score * self.WEIGHTS.get(label, 1.0)
            for label, score in scores.items()
        )

    def _bucket_from_score(self, score: float) -> SeverityLevel:
        """
        Convert weighted score to severity bucket.
        """
        if score >= self.BUCKET_THRESHOLDS[SeverityLevel.HIGH]:
            return SeverityLevel.HIGH
        if score >= self.BUCKET_THRESHOLDS[SeverityLevel.MEDIUM]:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW
