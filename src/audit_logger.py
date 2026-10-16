
import json
from datetime import datetime, timezone
from pathlib import Path


class AuditLogger:
    """Append decision records to a local JSON Lines audit file."""

    def __init__(self, log_path="logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, message, result):
        entry = {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "message_id": (
                message.get("message_id")
                if isinstance(message, dict)
                else None
            ),
            "message_type": (
                message.get("message_type")
                if isinstance(message, dict)
                else None
            ),
            "accepted": result["accepted"],
            "reason": result["reason"],
        }

        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\n")

        return entry
