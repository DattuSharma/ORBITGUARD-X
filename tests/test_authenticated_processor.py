from datetime import datetime, timezone

from src.authentication import sign_message
from src.audit_logger import AuditLogger
from src.authenticated_processor import AuthenticatedMessageProcessor


TEST_KEY = "ORBITGUARD-TEST-KEY-ONLY"


def make_message(sequence=1):
    return {
        "message_id": "AUTH-SIM-001",
        "message_type": "TELEMETRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": sequence,
        "payload": {"temperature_c": 24.5},
    }


def make_processor(tmp_path):
    logger = AuditLogger(tmp_path / "authenticated_audit.jsonl")
    return AuthenticatedMessageProcessor(TEST_KEY, audit_logger=logger)


def test_valid_signed_message_is_accepted(tmp_path):
    processor = make_processor(tmp_path)
    signed = sign_message(make_message(), TEST_KEY)

    result = processor.process(signed)

    assert result["accepted"] is True
    assert "Authentication" in result["reason"]


def test_forged_signature_is_rejected(tmp_path):
    processor = make_processor(tmp_path)
    signed = sign_message(make_message(), TEST_KEY)
    signed["auth_tag"] = "0" * 64

    result = processor.process(signed)

    assert result["accepted"] is False
    assert "Authentication failed" in result["reason"]


def test_modified_payload_is_rejected(tmp_path):
    processor = make_processor(tmp_path)
    signed = sign_message(make_message(), TEST_KEY)
    signed["payload"]["temperature_c"] = 30

    result = processor.process(signed)

    assert result["accepted"] is False
    assert "Authentication failed" in result["reason"]


def test_missing_signature_is_rejected(tmp_path):
    processor = make_processor(tmp_path)

    result = processor.process(make_message())

    assert result["accepted"] is False
    assert "Authentication failed" in result["reason"]


def test_forged_high_sequence_does_not_block_legitimate_message(tmp_path):
    processor = make_processor(tmp_path)

    forged = sign_message(make_message(sequence=999), TEST_KEY)
    forged["auth_tag"] = "0" * 64
    assert processor.process(forged)["accepted"] is False

    legitimate = sign_message(make_message(sequence=1), TEST_KEY)
    result = processor.process(legitimate)

    assert result["accepted"] is True


def test_replayed_signed_message_is_rejected(tmp_path):
    processor = make_processor(tmp_path)
    signed = sign_message(make_message(sequence=1), TEST_KEY)

    assert processor.process(signed)["accepted"] is True
    result = processor.process(signed)

    assert result["accepted"] is False
    assert "Replay" in result["reason"]
