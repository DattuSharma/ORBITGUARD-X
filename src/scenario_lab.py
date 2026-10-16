
from copy import deepcopy
from datetime import datetime, timedelta, timezone


def make_baseline_message():
    """Create a valid synthetic telemetry message."""
    return {
        "message_id": "LAB-001",
        "message_type": "TELEMETRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 1,
        "payload": {"temperature_c": 24.5},
    }


def build_scenario(scenario_name):
    """Build a named, controlled test case using synthetic data."""
    message = make_baseline_message()

    if scenario_name == "valid":
        pass

    elif scenario_name == "temperature_out_of_range":
        message["payload"]["temperature_c"] = 999

    elif scenario_name == "unauthorized_command":
        message["message_type"] = "COMMAND"
        message["payload"] = {"command": "OVERRIDE_ALL"}

    elif scenario_name == "missing_required_field":
        del message["sequence"]

    elif scenario_name == "stale_timestamp":
        old_time = datetime.now(timezone.utc) - timedelta(minutes=20)
        message["timestamp"] = old_time.isoformat()

    elif scenario_name == "negative_sequence":
        message["sequence"] = -1

    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    return deepcopy(message)


SCENARIO_DESCRIPTIONS = {
    "valid": "Valid telemetry baseline",
    "temperature_out_of_range": "Out-of-range telemetry value",
    "unauthorized_command": "Command outside the allowlist",
    "missing_required_field": "Required sequence field missing",
    "stale_timestamp": "Message timestamp is too old",
    "negative_sequence": "Invalid negative sequence number",
}
