
from src.validator import validate_message
from src.audit_logger import AuditLogger


class MessageProcessor:
    """Validate synthetic messages and log each decision."""

    def __init__(self, audit_logger=None):
        self.last_sequence = {}
        self.audit_logger = audit_logger or AuditLogger()

    def process(self, message):
        result = validate_message(message)

        if result["accepted"]:
            sender_id = message["message_id"]
            sequence = message["sequence"]
            previous = self.last_sequence.get(sender_id)

            if previous is not None and sequence <= previous:
                result = {
                    "accepted": False,
                    "reason": (
                        f"Replay or out-of-order sequence: {sequence}; "
                        f"last accepted sequence was {previous}."
                    ),
                }
            else:
                self.last_sequence[sender_id] = sequence
                result = {
                    "accepted": True,
                    "reason": "Schema, policy, and sequence checks passed.",
                }

        self.audit_logger.record(message, result)
        return result
