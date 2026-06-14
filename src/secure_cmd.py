import os
import json
import time
import hmac
import hashlib

KEY = os.getenv("AROS_CMD_KEY", "aros-s-dev-key").encode()
MAX_AGE = 5.0   #seconds; reject stale commands (replay protection)


def _canon(body: dict) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def sign(action: str, **fields) -> bytes:
    """Build a signed command datagram for the given action + fields."""
    body = {"action": action, "ts": time.time(), **fields}
    mac = hmac.new(KEY, _canon(body), hashlib.sha256).hexdigest()
    return json.dumps({"body": body, "mac": mac}).encode()


def verify(raw: bytes):
    """Return the command body if authentic AND fresh, otherwise None."""
    try:
        msg = json.loads(raw.decode())
        body, mac = msg["body"], msg["mac"]
    except Exception:
        return None
    good = hmac.new(KEY, _canon(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(good, mac):
        return None                                   #forged / wrong key
    if abs(time.time() - body.get("ts", 0)) > MAX_AGE:
        return None                                   #stale / replayed
    return body
