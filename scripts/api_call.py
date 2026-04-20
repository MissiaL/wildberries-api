from pathlib import Path
import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request


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
SENSITIVE_PATTERN = re.compile(r"(token|key|secret|password|authorization)[=:]\s*\S+", re.IGNORECASE)
PATH_PATTERN = re.compile(r"/(?:Users|home|opt|var|etc|tmp)/\S+")


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


def sanitize_error(text):
    text = SENSITIVE_PATTERN.sub(r"\1=***", text)
    return PATH_PATTERN.sub("<path>", text)


def make_request(method, url, params=None, body=None, headers=None):
    parsed = validate_url(url)
    extra_headers = filter_headers(headers)
    token = get_token()
    final_url = parsed.geturl()
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        final_url = f"{final_url}?{query}"

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(final_url, data=data, method=method)
    request.add_header("Authorization", token)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    for key, value in extra_headers.items():
        request.add_header(key, value)

    response = urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=30)
    return json.loads(response.read().decode("utf-8"))


def run_cli(argv=None):
    parser = argparse.ArgumentParser(description="Production WB API client")
    parser.add_argument("--method", required=True, choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    parser.add_argument("--url", required=True)
    parser.add_argument("--params")
    parser.add_argument("--body")
    parser.add_argument("--headers")
    args = parser.parse_args(argv)

    try:
        result = make_request(
            args.method,
            args.url,
            params=json.loads(args.params) if args.params else None,
            body=json.loads(args.body) if args.body else None,
            headers=json.loads(args.headers) if args.headers else None,
        )
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        json.dump(
            {"error": True, "status": exc.code, "message": sanitize_error(payload)},
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
        raise SystemExit(1)
    except Exception as exc:
        json.dump({"error": True, "message": sanitize_error(str(exc))}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        raise SystemExit(1)
