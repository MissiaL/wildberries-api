from pathlib import Path
import argparse
import base64
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "assets" / "openapi" / "host-allowlist.json"
OPENAPI_DIR = ROOT / "assets" / "openapi"
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
RATE_LIMIT_HEADERS = {
    "x-ratelimit-remaining": "remaining",
    "x-ratelimit-retry": "retryAfterSeconds",
    "x-ratelimit-limit": "burstLimit",
    "x-ratelimit-reset": "resetAfterSeconds",
}
TOKEN_TYPES = {
    1: "basic",
    2: "test",
    3: "personal",
    4: "service",
}
TOKEN_TYPE_LABELS = {
    "basic": "Базовый",
    "test": "Тестовый",
    "personal": "Персональный",
    "service": "Сервисный",
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


def detect_token_type(token):
    try:
        payload_segment = token.split(".")[1]
        padding = "=" * (-len(payload_segment) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_segment + padding))
        return TOKEN_TYPES.get(int(payload.get("acc")))
    except (IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None


def path_template_matches(template, actual_path):
    pattern = re.escape(template)
    pattern = re.sub(r"\\\{[^{}]+\\\}", r"[^/]+", pattern)
    return re.fullmatch(pattern, actual_path) is not None


def load_operation_rate_limit(method, url):
    actual_path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    matches = []
    for schema_path in OPENAPI_DIR.glob("*.json"):
        if schema_path.name in {
            "host-allowlist.json",
            "manifest.json",
            "rate-limit-manifest.json",
        }:
            continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for template, operations in schema.get("paths", {}).items():
            operation = operations.get(method.lower())
            if operation and path_template_matches(template, actual_path):
                rate_limit = operation.get("x-wb-rate-limits")
                if rate_limit:
                    matches.append((template, rate_limit))
    if not matches:
        return None
    exact = [rate_limit for template, rate_limit in matches if template == actual_path]
    if exact:
        return exact[0]
    matches.sort(key=lambda item: len(item[0]), reverse=True)
    return matches[0][1]


def select_token_limit(rate_limit, token_type):
    limits = rate_limit.get("limits")
    if not limits:
        return None
    rows_with_type = [row for row in limits if row.get("Тип")]
    if not rows_with_type:
        return limits[0]
    expected = TOKEN_TYPE_LABELS.get(token_type)
    if expected:
        for row in rows_with_type:
            if row.get("Тип") == expected:
                return row
    return None


def configured_rate_limit(method, url, token):
    rate_limit = load_operation_rate_limit(method, url)
    if not rate_limit:
        return None
    token_type = detect_token_type(token)
    selected = select_token_limit(rate_limit, token_type)
    return {
        "tokenType": token_type or "unknown",
        "scope": rate_limit.get("scope"),
        "limit": selected,
        "note": rate_limit.get("note") or rate_limit.get("raw"),
        "source": rate_limit.get("source"),
        "verifiedAt": rate_limit.get("verifiedAt"),
    }


def sanitize_error(text):
    text = SENSITIVE_PATTERN.sub(r"\1=***", text)
    return PATH_PATTERN.sub("<path>", text)


def extract_rate_limit_headers(headers):
    if not headers:
        return {}
    normalized = {key.lower(): value for key, value in headers.items()}
    return {
        output_key: normalized[header_name]
        for header_name, output_key in RATE_LIMIT_HEADERS.items()
        if header_name in normalized
    }


def retry_delay_seconds(error, retry_number):
    rate_limit = extract_rate_limit_headers(error.headers)
    raw_delay = rate_limit.get("retryAfterSeconds")
    if raw_delay is not None:
        try:
            return max(0.0, float(str(raw_delay).replace(",", ".")))
        except ValueError:
            pass
    return float(2 ** (retry_number - 1))


def make_request(
    method,
    url,
    params=None,
    body=None,
    headers=None,
    max_retries=3,
    max_wait=60.0,
    sleep_func=time.sleep,
    return_headers=False,
):
    parsed = validate_url(url)
    extra_headers = filter_headers(headers)
    token = get_token()
    final_url = parsed.geturl()
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        split = urllib.parse.urlsplit(final_url)
        merged_query = "&".join(filter(None, [split.query, query]))
        final_url = urllib.parse.urlunsplit((split.scheme, split.netloc, split.path, merged_query, split.fragment))

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

    retry_number = 0
    while True:
        try:
            response = urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=30)
            raw_payload = response.read().decode("utf-8")
            payload = json.loads(raw_payload) if raw_payload else None
            rate_limit = extract_rate_limit_headers(getattr(response, "headers", None))
            return (payload, rate_limit) if return_headers else payload
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or retry_number >= max_retries:
                raise
            retry_number += 1
            delay = retry_delay_seconds(exc, retry_number)
            if delay > max_wait:
                raise
            sleep_func(delay)


def run_cli(argv=None):
    parser = argparse.ArgumentParser(description="Production WB API client")
    parser.add_argument("--method", required=True, choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    parser.add_argument("--url", required=True)
    parser.add_argument("--params")
    parser.add_argument("--body")
    parser.add_argument("--headers")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries after HTTP 429 (default: 3; use 0 to disable)",
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=60.0,
        help="Do not sleep longer than this many seconds for one retry (default: 60)",
    )
    parser.add_argument(
        "--show-rate-limit",
        action="store_true",
        help="Print the verified local limit for this method/token type without calling WB",
    )
    args = parser.parse_args(argv)
    configured_limit = None

    try:
        if args.max_retries < 0 or args.max_wait < 0:
            raise ValueError("--max-retries and --max-wait must be non-negative")
        token = get_token()
        token_type = detect_token_type(token)
        if token_type == "test":
            raise ValueError("Test tokens are sandbox-only and blocked by this production client")
        configured_limit = configured_rate_limit(args.method, args.url, token)
        if args.show_rate_limit:
            if configured_limit is None:
                raise ValueError("No verified local rate limit found for this method and URL")
            json.dump(
                {"configuredRateLimit": configured_limit},
                sys.stdout,
                ensure_ascii=False,
                indent=2,
            )
            sys.stdout.write("\n")
            return
        result, rate_limit = make_request(
            args.method,
            args.url,
            params=json.loads(args.params) if args.params else None,
            body=json.loads(args.body) if args.body else None,
            headers=json.loads(args.headers) if args.headers else None,
            max_retries=args.max_retries,
            max_wait=args.max_wait,
            return_headers=True,
        )
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        metadata = {}
        if configured_limit:
            metadata["configuredRateLimit"] = configured_limit
        if rate_limit:
            metadata["rateLimit"] = rate_limit
        if metadata:
            json.dump(metadata, sys.stderr, ensure_ascii=False)
            sys.stderr.write("\n")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        error_payload = {"error": True, "status": exc.code, "message": sanitize_error(payload)}
        rate_limit = extract_rate_limit_headers(exc.headers)
        if rate_limit:
            error_payload["rateLimit"] = rate_limit
        if configured_limit:
            error_payload["configuredRateLimit"] = configured_limit
        json.dump(error_payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        raise SystemExit(1)
    except Exception as exc:
        json.dump({"error": True, "message": sanitize_error(str(exc))}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        raise SystemExit(1)


if __name__ == "__main__":
    run_cli()
