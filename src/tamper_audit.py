
import hashlib
import json
from pathlib import Path


class TamperEvidentAudit:
    """Create and verify a hash-linked JSON Lines audit log."""

    def __init__(self, log_path):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash_record(record):
        canonical = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def append(self, event):
        records = self._read_records()

        previous_hash = (
            records[-1]["record_hash"] if records else "GENESIS"
        )

        record = {
            "event": event,
            "previous_hash": previous_hash,
        }
        record["record_hash"] = self._hash_record(record)

        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

        return record

    def _read_records(self):
        if not self.log_path.exists():
            return []

        records = []
        with self.log_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    records.append(json.loads(line))

        return records

    def verify(self):
        records = self._read_records()
        expected_previous = "GENESIS"

        for index, record in enumerate(records):
            stored_hash = record.get("record_hash")
            previous_hash = record.get("previous_hash")

            if previous_hash != expected_previous:
                return {
                    "valid": False,
                    "record": index + 1,
                    "reason": "Previous-record hash mismatch.",
                }

            unsigned_record = {
                "event": record.get("event"),
                "previous_hash": previous_hash,
            }

            calculated_hash = self._hash_record(unsigned_record)

            if stored_hash != calculated_hash:
                return {
                    "valid": False,
                    "record": index + 1,
                    "reason": "Record content or hash was modified.",
                }

            expected_previous = stored_hash

        return {
            "valid": True,
            "records_checked": len(records),
            "reason": "All record hashes and links are valid.",
        }
