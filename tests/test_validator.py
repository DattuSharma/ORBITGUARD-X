
from datetime import datetime, timezone

from src.validator import validate_message


def valid_telemetry():
    return {
        "message_id": "TEST-001",
        "message_type": "TELEMETRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 1,
        "payload": {"temperature_c": 24.5},
    }


def test_valid_telemetry_is_accepted():
    result = validate_message(valid_telemetry())
    assert result["accepted"] is True


def test_unknown_command_is_rejected():
    message = valid_telemetry()
    message["message_type"] = "COMMAND"
    message["payload"] = {"command": "LAUNCH"}
    result = validate_message(message)
    assert result["accepted"] is False


def test_out_of_range_temperature_is_rejected():
    message = valid_telemetry()
    message["payload"]["temperature_c"] = 999
    result = validate_message(message)
    assert result["accepted"] is False


def test_missing_field_is_rejected():
    message = valid_telemetry()
    del message["sequence"]
    result = validate_message(message)
    assert result["accepted"] is False

