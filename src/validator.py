
from datetime import datetime, timezone

ALLOWED_MESSAGE_TYPES = {"TELEMETRY", "COMMAND"}
ALLOWED_COMMANDS = {"PING", "STATUS", "SAFE_MODE"}


def validate_message(message):
    """Validate a synthetic telemetry or command message."""

    def reject(reason):
        return {"accepted": False, "reason": reason}

    if not isinstance(message, dict):
        return reject("Message must be a JSON object.")

    required = {
        "message_id",
        "message_type",
        "timestamp",
        "sequence",
        "payload",
    }

    missing = required - message.keys()
    if missing:
        return reject(f"Missing fields: {', '.join(sorted(missing))}.")

    if not isinstance(message["message_id"], str) or not message["message_id"].strip():
        return reject("message_id must be a non-empty string.")

    message_type = message["message_type"]
    if not isinstance(message_type, str) or message_type not in ALLOWED_MESSAGE_TYPES:
        return reject("Unsupported message_type.")

    timestamp = message["timestamp"]
    if not isinstance(timestamp, str):
        return reject("Timestamp must be an ISO 8601 string.")

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return reject("Timestamp must include a timezone.")
    except ValueError:
        return reject("Invalid timestamp.")

    age = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()

    if age > 300:
        return reject("Message is stale.")

    if age < -60:
        return reject("Timestamp is too far in the future.")

    sequence = message["sequence"]
    if type(sequence) is not int or sequence < 0:
        return reject("Sequence must be a non-negative integer.")

    payload = message["payload"]
    if not isinstance(payload, dict):
        return reject("Payload must be a JSON object.")

    if message_type == "TELEMETRY":
        temperature = payload.get("temperature_c")
        if type(temperature) not in (int, float):
            return reject("temperature_c must be numeric.")
        if not -100 <= temperature <= 200:
            return reject("Temperature is outside the permitted range.")

    if message_type == "COMMAND":
        command = payload.get("command")
        if not isinstance(command, str) or command not in ALLOWED_COMMANDS:
            return reject("Command is not allowed.")

    return {
        "accepted": True,
        "reason": "Message passed validation."
    }
