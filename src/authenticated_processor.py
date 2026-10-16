from src.validator import validate_message
from src.audit_logger import AuditLogger
from src.authentication import verify_message


class AuthenticatedMessageProcessor:
    """Authenticate synthetic messages before validation and sequence checks."""

    def __init__(self, auth_key, audit_logger=None):
        if not isinstance(auth_key, (str, bytes)) or not auth_key:
            raise ValueError("A non-empty HMAC key is required.")

        self.auth_key = auth_key
        self.audit_logger = audit_logger or AuditLogger()
        self.last_sequence = {}

    def process(self, message):
        if not verify_message(message, self.auth_key):
            result = {
                "accepted": False,
                "reason": "Authentication failed: missing or invalid HMAC tag.",
            }
            self.audit_logger.record(message, result)
            return result

        result = validate_message(message)

        if result["accepted"]:
            message_id = message["message_id"]
            sequence = message["sequence"]
            previous = self.last_sequence.get(message_id)

            if previous is not None and sequence <= previous:
                result = {
                    "accepted": False,
                    "reason": (
                        f"Replay or out-of-order sequence: {sequence}; "
                        f"last accepted sequence was {previous}."
                    ),
                }
            else:
                self.last_sequence[message_id] = sequence
                result = {
                    "accepted": True,
                    "reason": (
                        "Authentication, schema, policy, and sequence checks passed."
                    ),
                }

        self.audit_logger.record(message, result)
        return result
