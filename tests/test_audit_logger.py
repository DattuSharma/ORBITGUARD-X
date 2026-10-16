
import json

from src.audit_logger import AuditLogger


def test_audit_logger_records_acceptance(tmp_path):
    logger = AuditLogger(tmp_path / "audit.jsonl")

    message = {
        "message_id": "SIM-001",
        "message_type": "TELEMETRY",
    }
    result = {
        "accepted": True,
        "reason": "Validation passed.",
    }

    logger.record(message, result)

    lines = (tmp_path / "audit.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["message_id"] == "SIM-001"
    assert entry["accepted"] is True
    assert entry["reason"] == "Validation passed."


def test_audit_logger_records_rejection(tmp_path):
    logger = AuditLogger(tmp_path / "audit.jsonl")

    logger.record(
        {"message_id": "SIM-002"},
        {"accepted": False, "reason": "Invalid sequence."},
    )

    entry = json.loads(
        (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    )

    assert entry["accepted"] is False
    assert entry["reason"] == "Invalid sequence."
