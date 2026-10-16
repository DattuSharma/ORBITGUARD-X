
from datetime import datetime, timezone

from src.audit_logger import AuditLogger
from src.message_processor import MessageProcessor


def make_message(sequence):
    return {
        "message_id": "SIM-001",
        "message_type": "TELEMETRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": sequence,
        "payload": {"temperature_c": 24.5},
    }


def make_processor(tmp_path):
    logger = AuditLogger(tmp_path / "audit.jsonl")
    return MessageProcessor(audit_logger=logger)


def test_first_message_is_accepted(tmp_path):
    processor = make_processor(tmp_path)
    assert processor.process(make_message(1))["accepted"] is True


def test_increasing_sequence_is_accepted(tmp_path):
    processor = make_processor(tmp_path)
    processor.process(make_message(1))
    assert processor.process(make_message(2))["accepted"] is True


def test_replayed_sequence_is_rejected(tmp_path):
    processor = make_processor(tmp_path)
    processor.process(make_message(1))
    result = processor.process(make_message(1))
    assert result["accepted"] is False
    assert "Replay" in result["reason"]


def test_invalid_message_does_not_update_sequence(tmp_path):
    processor = make_processor(tmp_path)
    bad_message = make_message(1)
    bad_message["payload"]["temperature_c"] = 999

    assert processor.process(bad_message)["accepted"] is False
    assert processor.process(make_message(1))["accepted"] is True
