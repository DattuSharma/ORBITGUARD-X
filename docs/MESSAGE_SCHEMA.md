# ORBITGUARD X — Synthetic Message Schema

## Scope

A local educational simulator using synthetic messages only.
It does not connect to satellites, ground stations, or operational systems.

## Common fields

| Field | Type | Rule |
|---|---|---|
| message_id | String | Required and non-empty |
| message_type | String | TELEMETRY or COMMAND |
| timestamp | ISO 8601 string | Must include a timezone; maximum age 300 seconds; maximum future offset 60 seconds |
| sequence | Integer | Non-negative integer |
| payload | JSON object | Content depends on message_type |

## TELEMETRY payload

| Field | Type | Rule |
|---|---|---|
| temperature_c | Number | Between -100 and 200, inclusive |

## COMMAND payload

| Field | Type | Rule |
|---|---|---|
| command | String | PING, STATUS, or SAFE_MODE |

## Sequence and replay protection

For each message_id, the processor accepts only a sequence number greater
than the last accepted sequence number. Repeated or lower sequence numbers
are rejected. Sequence state is held in memory and resets on restart.

## Optional HMAC authentication

The separate AuthenticatedMessageProcessor verifies HMAC-SHA256 tags using
Python's standard hmac and hashlib libraries. The authentication tag is
computed over canonical JSON, with keys sorted and compact separators used.

The auth_tag field contains the hexadecimal HMAC-SHA256 digest. Verification
uses hmac.compare_digest. Authentication is checked before schema validation
and before sequence state can change.

Messages signed with the wrong key, messages with missing tags, and modified
messages are rejected.

## Key-handling limitations

The tests use a demonstration-only shared key. It is not a production secret.
A real deployment would need secure key provisioning, storage, rotation, and
separate keys for different senders. HMAC authenticates possession of a
shared secret; it does not encrypt messages or provide non-repudiation.

## Current integration status

The authenticated processor and its tests are implemented as a separate
module. The existing dashboard/default processor has not yet been changed
to require authentication. Do not claim that all dashboard messages are
authenticated.

## Safety

All inputs are synthetic. This prototype has no live command channel and is
not a certified aerospace security product.
