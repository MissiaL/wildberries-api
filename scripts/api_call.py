from pathlib import Path
import json
import os
import urllib.parse


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "assets" / "openapi" / "host-allowlist.json"
BLOCKED_HEADERS = {
    "authorization",
    "cookie",
    "host",
    "proxy-authorization",
    "x-forwarded-for",
    "x-real-ip",
}


def load_allowlisted_hosts():
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return set(payload["hosts"])


def validate_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Blocked URL scheme: {parsed.scheme}")
    if parsed.port not in (None, 443):
        raise ValueError(f"Blocked port: {parsed.port}")
    if parsed.hostname not in load_allowlisted_hosts():
        raise ValueError(f"Blocked host: {parsed.hostname}")
    return parsed


def filter_headers(headers):
    blocked = [key for key in headers or {} if key.lower() in BLOCKED_HEADERS]
    if blocked:
        raise ValueError(f"Blocked headers: {', '.join(blocked)}")
    return headers or {}


def get_token():
    token = os.environ.get("WB_API_TOKEN", "").strip()
    if not token:
        raise ValueError("WB_API_TOKEN is required")
    return token
