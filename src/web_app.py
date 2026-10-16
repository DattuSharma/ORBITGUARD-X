
from flask import Flask, redirect, render_template_string, url_for
from pathlib import Path
from datetime import datetime, timezone
import json

from src.audit_logger import AuditLogger
from src.message_processor import MessageProcessor
from src.validator import validate_message
from src.scenario_lab import build_scenario, SCENARIO_DESCRIPTIONS
from src.tamper_audit import TamperEvidentAudit
from src.live_test import live_test

app = Flask(__name__)
app.register_blueprint(live_test)

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
DASHBOARD_LOG = LOG_DIR / "dashboard_audit.jsonl"
TAMPER_LOG = LOG_DIR / "tamper_audit.jsonl"

STYLE = """
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 30px 16px;
    background: #08111f;
    color: #e8eef8;
    font-family: Arial, sans-serif;
}
main { max-width: 1100px; margin: auto; }
header, section, .stat {
    background: #111d30;
    border: 1px solid #263853;
    border-radius: 14px;
}
header { padding: 25px; margin-bottom: 18px; }
h1 { margin: 0 0 8px; color: #83c5ff; }
h2 { font-size: 19px; }
p { line-height: 1.6; color: #b7c7dc; }
.notice {
    border-left: 4px solid #e6b450;
    background: #2a2518;
    padding: 12px;
    border-radius: 5px;
}
.stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 18px 0;
}
.stat { padding: 18px; }
.stat span { display: block; color: #a9bad0; font-size: 13px; }
.stat strong { display: block; font-size: 32px; margin-top: 8px; }
section { padding: 22px; margin: 18px 0; }
.actions { display: flex; flex-wrap: wrap; gap: 10px; }
button, .button {
    background: #1769aa;
    color: white;
    padding: 12px 16px;
    border: 0;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    font-size: 14px;
}
.secondary { background: #263853; }
input, select {
    width: 100%;
    max-width: 500px;
    padding: 11px;
    margin: 8px 0 16px;
    color: #edf4ff;
    background: #091525;
    border: 1px solid #38506e;
    border-radius: 7px;
}
table { width: 100%; border-collapse: collapse; }
th, td {
    text-align: left;
    padding: 11px 9px;
    border-bottom: 1px solid #263853;
    font-size: 13px;
    overflow-wrap: anywhere;
}
th { color: #9bcfff; }
.accept { color: #67e8a5; font-weight: bold; }
.reject { color: #ff8c96; font-weight: bold; }
pre {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    background: #091525;
    padding: 14px;
    border-radius: 8px;
}
@media (max-width: 650px) {
    .stats { grid-template-columns: 1fr; }
    table { font-size: 12px; }
    th, td { padding: 8px 5px; }
}
</style>
"""

DASHBOARD_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ORBITGUARD X | Mission Trust Console</title>
""" + STYLE + """
</head>
<body>
<main>
<header>
    <h1>ORBITGUARD X</h1>
    <p><strong>Mission Trust Console</strong><br>
    Synthetic telemetry and command validation simulator</p>
    <p class="notice"><strong>LOCAL SIMULATION</strong><br>
    Simulation mode only. This prototype processes generated test messages.
    It does not connect to satellites or operational command systems.</p>
</header>

<div class="stats">
    <div class="stat"><span>MESSAGES PROCESSED</span>
        <strong>{{ stats.processed }}</strong></div>
    <div class="stat"><span>ACCEPTED</span>
        <strong class="accept">{{ stats.accepted }}</strong></div>
    <div class="stat"><span>REJECTED</span>
        <strong class="reject">{{ stats.rejected }}</strong></div>
</div>

<section>
    <div class="actions">
        <form action="{{ url_for('run_demo') }}" method="post">
            <button type="submit">▶ Run Synthetic Validation Demo</button>
        </form>
        <a class="button secondary" href="{{ url_for('scenario_lab_page') }}">
            ◈ Threat Scenario Lab
        </a>
        <a class="button secondary" href="{{ url_for('live_test.live_test_page') }}">
            LIVE MESSAGE TESTER
        </a>
        <a class="button secondary" href="{{ url_for('audit_integrity_page') }}">
            ✓ Verify Audit Integrity
        </a>
    </div>
    {% if notice %}
    <p>{{ notice }}</p>
    {% endif %}
</section>

<section>
<h2>Message Decision History</h2>
{% if records %}
<div style="overflow-x:auto">
<table>
<thead><tr>
<th>Decision time (UTC)</th><th>Message ID</th><th>Type</th>
<th>Decision</th><th>Reason</th>
</tr></thead>
<tbody>
{% for item in records %}
<tr>
<td>{{ item.timestamp }}</td>
<td>{{ item.message_id }}</td>
<td>{{ item.message_type }}</td>
<td class="{{ 'accept' if item.accepted else 'reject' }}">
{{ 'ACCEPT' if item.accepted else 'REJECT' }}</td>
<td>{{ item.reason }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
{% else %}
<p>No demo records yet. Run the synthetic validation demo to begin.</p>
{% endif %}
</section>
</main>
</body>
</html>
"""

SCENARIO_PAGE = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Threat Scenario Lab</title>
""" + STYLE + """
</head>
<body><main>
<header>
<h1>Threat Scenario Lab</h1>
<p>Test synthetic messages against the validation rules.</p>
<p class="notice">Simulation only. No operational systems are contacted.</p>
<a class="button secondary" href="{{ url_for('index_route') }}">← Dashboard</a>
</header>

<section>
<form method="post">
<label for="scenario"><strong>Choose a test scenario</strong></label><br>
<select id="scenario" name="scenario">
{% for key, description in scenarios.items() %}
<option value="{{ key }}" {% if selected == key %}selected{% endif %}>
{{ description }}
</option>
{% endfor %}
</select><br>
<button type="submit">Run Selected Scenario</button>
</form>
</section>

{% if result %}
<section>
<h2>Scenario Result</h2>
<p class="{{ 'accept' if result.accepted else 'reject' }}">
{{ 'ACCEPTED' if result.accepted else 'REJECTED' }}
</p>
<p><strong>Reason:</strong> {{ result.reason }}</p>
<h3>Generated Synthetic Message</h3>
<pre>{{ message_json }}</pre>
</section>
{% endif %}
</main></body></html>
"""

INTEGRITY_PAGE = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Audit Integrity</title>
""" + STYLE + """
</head>
<body><main>
<header>
<h1>Audit Integrity Verification</h1>
<p>Verify the hash-linked synthetic audit records.</p>
<a class="button secondary" href="{{ url_for('index_route') }}">← Dashboard</a>
</header>
<section>
{% if error %}
<p class="reject">{{ error }}</p>
{% else %}
<h2 class="{{ 'accept' if result.valid else 'reject' }}">
{{ 'INTEGRITY CHECK PASSED' if result.valid else 'INTEGRITY CHECK FAILED' }}
</h2>
<p>{{ result.reason }}</p>
<p>Records checked: {{ result.records_checked if result.valid else result.record }}</p>
{% endif %}
<p><strong>Important limitation:</strong> A local hash chain can detect accidental
or partial modification, but it cannot prove authenticity against an attacker
who can rewrite the entire file and recompute every hash. External anchoring
and access controls would be needed for stronger guarantees.</p>
</section>
</main></body></html>
"""


def read_jsonl(path):
    if not path.exists():
        return []

    records = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def get_dashboard_records():
    return read_jsonl(DASHBOARD_LOG)


def index():
    records = get_dashboard_records()
    accepted = sum(1 for record in records if record.get("accepted") is True)
    rejected = sum(1 for record in records if record.get("accepted") is False)

    stats = {
        "processed": accepted + rejected,
        "accepted": accepted,
        "rejected": rejected,
    }
    return render_template_string(
        DASHBOARD_PAGE, records=list(reversed(records)), stats=stats, notice=""
    )


def run_synthetic_scenarios():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Start a fresh demo audit trail each time the demo is run.
    for path in (DASHBOARD_LOG, TAMPER_LOG):
        if path.exists():
            path.unlink()

    processor = MessageProcessor(audit_logger=AuditLogger(DASHBOARD_LOG))
    tamper_audit = TamperEvidentAudit(TAMPER_LOG)

    # Scenario 1: valid telemetry.
    valid_telemetry = build_scenario("valid")
    valid_telemetry["message_id"] = "SIM-001"
    valid_telemetry["sequence"] = 1
    result = processor.process(valid_telemetry)
    tamper_audit.append({
        "message_id": valid_telemetry["message_id"],
        "accepted": result["accepted"],
        "reason": result["reason"],
    })

    # Scenario 2: invalid temperature.
    invalid_temperature = build_scenario("temperature_out_of_range")
    invalid_temperature["message_id"] = "SIM-002"
    invalid_temperature["sequence"] = 1
    result = processor.process(invalid_temperature)
    tamper_audit.append({
        "message_id": invalid_temperature["message_id"],
        "accepted": result["accepted"],
        "reason": result["reason"],
    })

    # Scenario 3: an allowed synthetic command.
    valid_command = {
        "message_id": "SIM-003",
        "message_type": "COMMAND",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 1,
        "payload": {"command": "PING"},
    }
    result = processor.process(valid_command)
    tamper_audit.append({
        "message_id": valid_command["message_id"],
        "accepted": result["accepted"],
        "reason": result["reason"],
    })

    # Scenario 4: replay the exact SIM-001 sequence number.
    replay_message = {
        "message_id": "SIM-001",
        "message_type": "TELEMETRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 1,
        "payload": {"temperature_c": 24.5},
    }
    result = processor.process(replay_message)
    tamper_audit.append({
        "message_id": replay_message["message_id"],
        "accepted": result["accepted"],
        "reason": result["reason"],
    })

    return tamper_audit.verify()


@app.route("/")
def index_route():
    return index()


@app.route("/run-demo", methods=["POST"])
def run_demo():
    run_synthetic_scenarios()
    return redirect(url_for("index_route"))


@app.route("/scenario-lab", methods=["GET", "POST"])
def scenario_lab_page():
    result = None
    message_json = None
    selected = "valid"
    message = None

    if __import__("flask").request.method == "POST":
        selected = __import__("flask").request.form.get("scenario", "valid")
        try:
            message = build_scenario(selected)
            result = validate_message(message)
            message_json = json.dumps(message, indent=2)
        except ValueError as exc:
            result = {"accepted": False, "reason": str(exc)}

    return render_template_string(
        SCENARIO_PAGE,
        scenarios=SCENARIO_DESCRIPTIONS,
        selected=selected,
        result=result,
        message_json=message_json,
    )


@app.route("/audit-integrity")
def audit_integrity_page():
    try:
        verifier = TamperEvidentAudit(TAMPER_LOG)
        result = verifier.verify()
        error = None
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        result = None
        error = f"Could not verify the audit log: {exc}"

    if result is None:
        result = {
            "valid": False,
            "records_checked": 0,
            "record": 0,
            "reason": "No integrity result available.",
        }

    return render_template_string(INTEGRITY_PAGE, result=result, error=error)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
