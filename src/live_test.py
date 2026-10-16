import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, render_template_string, request
from src.audit_logger import AuditLogger
from src.message_processor import MessageProcessor

live_test = Blueprint("live_test", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
LIVE_LOG = BASE_DIR / "logs" / "live_test_audit.jsonl"

# Keep replay protection active between requests while the app is running.
processor = MessageProcessor(
    audit_logger=AuditLogger(str(LIVE_LOG))
)

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ORBITGUARD X | Live Message Tester</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0; padding: 28px 16px; background: #08111f;
    color: #e8eef8; font-family: Arial, sans-serif;
}
main { max-width: 900px; margin: auto; }
section {
    background: #111d30; border: 1px solid #263853;
    border-radius: 14px; padding: 24px; margin-bottom: 18px;
}
h1 { color: #83c5ff; }
p { color: #b7c7dc; line-height: 1.6; }
textarea {
    width: 100%; min-height: 280px; padding: 14px;
    background: #07101c; color: #d9e8ff;
    border: 1px solid #385474; border-radius: 8px;
    font-family: Consolas, monospace; font-size: 14px;
}
button, a {
    display: inline-block; padding: 11px 16px; margin: 8px 6px 0 0;
    border: 0; border-radius: 7px; background: #1976d2;
    color: white; text-decoration: none; cursor: pointer;
    font-weight: bold;
}
.result { padding: 14px; border-radius: 8px; margin-top: 18px; }
.accept { background: #123b30; border: 1px solid #2c9b75; }
.reject { background: #451f29; border: 1px solid #d65a70; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; }
.small { font-size: 13px; }
</style>
</head>
<body>
<main>
<section>
<h1>ORBITGUARD X — Live Message Tester</h1>
<p>Test synthetic telemetry and command messages locally. No real satellite
or operational command system is connected.</p>
<a href="/">Back to Dashboard</a>
</section>

<section>
<form method="post">
<label for="message"><strong>Paste message JSON</strong></label>
<p class="small">Maximum input size: 10 KB.</p>
<textarea id="message" name="message" maxlength="10240" required>{{ message_text }}</textarea>
<br>
<button type="submit">Validate Message</button>
<button type="submit" name="load_example" value="1">Load Fresh Example</button>
</form>

{% if result %}
<div class="result {{ 'accept' if result.accepted else 'reject' }}">
<h2>{{ 'ACCEPTED' if result.accepted else 'REJECTED' }}</h2>
<p><strong>Reason:</strong> {{ result.reason }}</p>
{% if result.message_id is not none %}
<p><strong>Message ID:</strong> {{ result.message_id }}</p>
{% endif %}
</div>
{% endif %}
</section>

<section>
<h2>Message requirements</h2>
<pre>{
  "message_id": "JUDGE-001",
  "message_type": "TELEMETRY",
  "timestamp": "2026-10-16T12:00:00+00:00",
  "sequence": 1,
  "payload": {"temperature_c": 24.5}
}</pre>
<p class="small">Use a current timezone-aware timestamp. For replay testing,
submit an accepted message again with the same ID and sequence.</p>
</section>
</main>
</body>
</html>
"""


def fresh_example():
    now = datetime.now(timezone.utc)
    return {
        "message_id": f"JUDGE-{now.strftime('%Y%m%d%H%M%S%f')}",
        "message_type": "TELEMETRY",
        "timestamp": now.isoformat(),
        "sequence": 1,
        "payload": {"temperature_c": 24.5},
    }


@live_test.route("/live-test", methods=["GET", "POST"])
def live_test_page():
    result = None

    if request.method == "POST" and request.form.get("load_example") == "1":
        message_text = json.dumps(fresh_example(), indent=2)

    elif request.method == "POST":
        message_text = request.form.get("message", "")

        if len(message_text.encode("utf-8")) > 10240:
            result = {
                "accepted": False,
                "reason": "Input is too large. Maximum size is 10 KB.",
                "message_id": None,
            }
        else:
            try:
                message = json.loads(message_text)
                result = processor.process(message)
                result["message_id"] = (
                    message.get("message_id")
                    if isinstance(message, dict)
                    else None
                )
            except (json.JSONDecodeError, UnicodeError):
                result = {
                    "accepted": False,
                    "reason": "Invalid JSON. Check the syntax and try again.",
                    "message_id": None,
                }
    else:
        message_text = json.dumps(fresh_example(), indent=2)

    return render_template_string(
        PAGE,
        message_text=message_text,
        result=result,
    )
