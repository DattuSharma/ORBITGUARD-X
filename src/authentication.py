import hashlib
import hmac
import json

AUTH_TAG_FIELD = "auth_tag"


def _key_bytes(key):
    if isinstance(key, str):
        key = key.encode("utf-8")

    if not isinstance(key, bytes) or not key:
        raise ValueError("HMAC key must be a non-empty string or bytes.")

    return key


def _canonical_message(message):
    if not isinstance(message, dict):
        raise TypeError("Message must be a dictionary.")

    unsigned = dict(message)
    unsigned.pop(AUTH_TAG_FIELD, None)

    return json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sign_message(message, key):
    """Return a copy of the message containing an HMAC-SHA256 tag."""
    secret = _key_bytes(key)
    body = _canonical_message(message)
    tag = hmac.new(secret, body, hashlib.sha256).hexdigest()

    signed = dict(message)
    signed[AUTH_TAG_FIELD] = tag
    return signed


def verify_message(message, key):
    """Verify the message tag using constant-time comparison."""
    if not isinstance(message, dict):
        return False

    tag = message.get(AUTH_TAG_FIELD)
    if not isinstance(tag, str):
        return False

    try:
        secret = _key_bytes(key)
        body = _canonical_message(message)
        expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    except (TypeError, ValueError):
        return False

    return hmac.compare_digest(expected, tag)
