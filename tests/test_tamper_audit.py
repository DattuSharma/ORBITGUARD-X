
import json

from src.tamper_audit import TamperEvidentAudit


def test_valid_audit_chain_passes(tmp_path):
    audit = TamperEvidentAudit(tmp_path / "audit.jsonl")

    audit.append({"message_id": "SIM-001", "decision": "ACCEPT"})
    audit.append({"message_id": "SIM-002", "decision": "REJECT"})

    result = audit.verify()

    assert result["valid"] is True
    assert result["records_checked"] == 2


def test_modified_record_is_detected(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = TamperEvidentAudit(path)

    audit.append({"message_id": "SIM-001", "decision": "ACCEPT"})

    record = json.loads(path.read_text(encoding="utf-8"))
    record["event"]["decision"] = "REJECT"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    result = audit.verify()

    assert result["valid"] is False
    assert result["record"] == 1


def test_modified_previous_hash_is_detected(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = TamperEvidentAudit(path)

    audit.append({"message_id": "SIM-001", "decision": "ACCEPT"})
    audit.append({"message_id": "SIM-002", "decision": "REJECT"})

    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    records[1]["previous_hash"] = "tampered"
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    result = audit.verify()

    assert result["valid"] is False
    assert result["record"] == 2
