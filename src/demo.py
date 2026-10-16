
import json
from datetime import datetime, timezone
from pathlib import Path

from src.audit_logger import AuditLogger
from src.message_processor import MessageProcessor


def make_message(message_id, sequence, message_type, payload):
    """Create a synthetic telemetry or command message."""
    return {
        "message_id": message_id,
        "message_type": message_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": sequence,
        "payload": payload,
    }


def main():
    """Run repeatable synthetic message validation scenarios."""

    audit_path = Path("logs/demo_audit.jsonl")
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    # Start this demo with a fresh, dedicated audit log.
    audit_path.write_text("", encoding="utf-8")

    audit_logger = AuditLogger(audit_path)
    processor = MessageProcessor(audit_logger=audit_logger)

    messages = [
        (
            "Valid telemetry",
            make_message(
                "SIM-001",
                1,
                "TELEMETRY",
                {"temperature_c": 24.5},
            ),
        ),
        (
            "Temperature out of range",
            make_message(
                "SIM-002",
                1,
                "TELEMETRY",
                {"temperature_c": 999},
            ),
        ),
        (
            "Valid command",
            make_message(
                "SIM-003",
                1,
                "COMMAND",
                {"command": "PING"},
            ),
        ),
        (
            "Repeated sequence",
            make_message(
                "SIM-001",
                1,
                "TELEMETRY",
                {"temperature_c": 25.0},
            ),
        ),
    ]

    print("=" * 64)
    print(" ORBITGUARD X | SYNTHETIC MESSAGE VALIDATION SIMULATOR")
    print("=" * 64)
    print("Mode: LOCAL SIMULATION ONLY")
    print("No connection to real satellite or operational systems.")
    print("-" * 64)

    accepted_count = 0
    rejected_count = 0

    for scenario, message in messages:
        result = processor.process(message)

        if result["accepted"]:
            status = "ACCEPT"
            accepted_count += 1
        else:
            status = "REJECT"
            rejected_count += 1

        print(f"\nScenario : {scenario}")
        print(f"Message  : {message['message_id']}")
        print(f"Type     : {message['message_type']}")
        print(f"Sequence : {message['sequence']}")
        print(f"Decision : {status}")
        print(f"Reason   : {result['reason']}")

    print("\n" + "=" * 64)
    print(" DEMO SUMMARY")
    print("=" * 64)
    print(f"Total processed : {accepted_count + rejected_count}")
    print(f"Accepted        : {accepted_count}")
    print(f"Rejected        : {rejected_count}")
    print(f"Audit file      : {audit_path}")

    print("\nAUDIT RECORDS")
    print("-" * 64)

    with audit_path.open("r", encoding="utf-8") as file:
        for line in file:
            record = json.loads(line)
            status = "ACCEPT" if record["accepted"] else "REJECT"

            print(
                f"{record['message_id']} | "
                f"{status} | "
                f"{record['reason']}"
            )

    print("\nDemo completed. Synthetic data only.")


if __name__ == "__main__":
    main()
