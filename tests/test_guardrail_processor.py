import pytest
from datetime import datetime
from src.processors.guardrail_processor import GuardrailProcessor
from src.models.conversation import Conversation
from src.models.violation import SeverityLevel

def test_toxic_text_detected():
    processor = GuardrailProcessor(threshold=0.5)
    conv = Conversation(
        conversation_id="test_001",
        text="You're an idiot!",
        timestamp=datetime.now(),
        speaker="user"
    )

    violation = processor.process_conversation(conv)
    assert violation is not None
    assert violation.severity in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH]

def test_clean_text_no_violation():
    processor = GuardrailProcessor(threshold=0.5)
    conv = Conversation(
        conversation_id="test_002",
        text="Thank you for your help!",
        timestamp=datetime.now(),
        speaker="user"
    )

    violation = processor.process_conversation(conv)
    assert violation is None
