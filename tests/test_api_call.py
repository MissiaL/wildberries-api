import io
import base64
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

import pytest

from scripts import api_call


def fake_jwt(payload):
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"header.{encoded}.signature"


def test_validate_url_rejects_non_allowlisted_host(tmp_path, monkeypatch):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)

    with pytest.raises(ValueError, match="Blocked host"):
        api_call.validate_url("https://evil.example.com/api/v1/data")


def test_validate_url_rejects_non_default_https_port(tmp_path, monkeypatch):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)

    with pytest.raises(ValueError, match="Blocked port"):
        api_call.validate_url("https://common-api.wildberries.ru:444/ping")


def test_filter_headers_blocks_sensitive_headers():
    with pytest.raises(ValueError, match="Blocked headers"):
        api_call.filter_headers({"Authorization": "abc"})


def test_get_token_fails_when_env_missing(monkeypatch):
    monkeypatch.delenv("WB_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="WB_API_TOKEN"):
        api_call.get_token()


@pytest.mark.parametrize(
    ("acc", "expected"),
    [(1, "basic"), (2, "test"), (3, "personal"), (4, "service")],
)
def test_detect_token_type_from_local_jwt_payload(acc, expected):
    assert api_call.detect_token_type(fake_jwt({"acc": acc})) == expected


def test_path_template_matches_operation_ids():
    assert api_call.path_template_matches(
        "/api/v3/orders/{orderId}/cancel",
        "/api/v3/orders/123/cancel",
    )
    assert not api_call.path_template_matches(
        "/api/v3/orders/{orderId}/cancel",
        "/api/v3/orders/123/status",
    )


def test_configured_rate_limit_selects_personal_row():
    profile = api_call.configured_rate_limit(
        "GET",
        "https://common-api.wildberries.ru/api/v1/seller-info",
        fake_jwt({"acc": 3}),
    )

    assert profile["tokenType"] == "personal"
    assert profile["limit"]["Тип"] == "Персональный"
    assert profile["limit"]["Интервал"] == "1 мин"
    assert profile["source"].startswith("https://dev.wildberries.ru/docs/openapi/api-information")


class DummyResponse:
    def __init__(self, payload, headers=None):
        self.payload = payload
        self.headers = headers or {}

    def read(self):
        if self.payload is None:
            return b""
        return json.dumps(self.payload).encode("utf-8")


def test_make_request_adds_authorization_and_json_headers(monkeypatch, tmp_path):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)
    monkeypatch.setenv("WB_API_TOKEN", "secret-token")

    captured = {}

    def fake_urlopen(request, context=None, timeout=30):
        captured["headers"] = dict(request.header_items())
        captured["method"] = request.get_method()
        return DummyResponse({"ok": True})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = api_call.make_request("POST", "https://common-api.wildberries.ru/ping", body={"x": 1})

    assert result == {"ok": True}
    assert captured["method"] == "POST"
    assert captured["headers"]["Authorization"] == "secret-token"
    assert captured["headers"]["Accept"] == "application/json"
    assert captured["headers"]["Content-type"] == "application/json"


def test_make_request_merges_existing_query_params(monkeypatch, tmp_path):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)
    monkeypatch.setenv("WB_API_TOKEN", "secret-token")

    captured = {}

    def fake_urlopen(request, context=None, timeout=30):
        captured["query"] = urllib.parse.urlsplit(request.full_url).query
        return DummyResponse({"ok": True})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    api_call.make_request(
        "GET",
        "https://common-api.wildberries.ru/ping?existing=1",
        params={"new": "2"},
    )

    assert captured["query"] == "existing=1&new=2"


def test_make_request_returns_rate_limit_headers_when_requested(monkeypatch, tmp_path):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)
    monkeypatch.setenv("WB_API_TOKEN", "secret-token")

    def fake_urlopen(request, context=None, timeout=30):
        return DummyResponse(
            {"ok": True},
            headers={"X-Ratelimit-Remaining": "4", "X-Ratelimit-Limit": "10"},
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result, rate_limit = api_call.make_request(
        "GET",
        "https://common-api.wildberries.ru/ping",
        return_headers=True,
    )

    assert result == {"ok": True}
    assert rate_limit == {"remaining": "4", "burstLimit": "10"}


def test_make_request_retries_429_after_header_delay(monkeypatch, tmp_path):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)
    monkeypatch.setenv("WB_API_TOKEN", "secret-token")
    calls = {"count": 0}
    delays = []

    def fake_urlopen(request, context=None, timeout=30):
        calls["count"] += 1
        if calls["count"] == 1:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=429,
                msg="Too Many Requests",
                hdrs={"X-Ratelimit-Retry": "2"},
                fp=io.BytesIO(b'{"detail":"slow down"}'),
            )
        return DummyResponse({"ok": True})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    result = api_call.make_request(
        "GET",
        "https://common-api.wildberries.ru/ping",
        sleep_func=delays.append,
    )

    assert result == {"ok": True}
    assert calls["count"] == 2
    assert delays == [2.0]


def test_make_request_does_not_sleep_past_max_wait(monkeypatch, tmp_path):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)
    monkeypatch.setenv("WB_API_TOKEN", "secret-token")
    delays = []

    def fake_urlopen(request, context=None, timeout=30):
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=429,
            msg="Too Many Requests",
            hdrs={"X-Ratelimit-Retry": "120", "X-Ratelimit-Reset": "180"},
            fp=io.BytesIO(b'{"detail":"slow down"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(urllib.error.HTTPError, match="HTTP Error 429"):
        api_call.make_request(
            "GET",
            "https://common-api.wildberries.ru/ping",
            max_wait=60,
            sleep_func=delays.append,
        )

    assert delays == []


def test_sanitize_error_masks_token_and_paths():
    text = "token=abc123 path=/Users/petr/dev/brainstorm/botclaw/file.txt"
    sanitized = api_call.sanitize_error(text)
    assert "abc123" not in sanitized
    assert "/Users/petr" not in sanitized
    assert "token=***" in sanitized


def test_http_error_returns_structured_payload(monkeypatch, tmp_path, capsys):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)
    monkeypatch.setenv("WB_API_TOKEN", "secret-token")

    error = urllib.error.HTTPError(
        url="https://common-api.wildberries.ru/ping",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b'{"detail":"token=abc123"}'),
    )

    def fake_urlopen(request, context=None, timeout=30):
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(SystemExit, match="1"):
        api_call.run_cli(["--method", "GET", "--url", "https://common-api.wildberries.ru/ping"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] is True
    assert payload["status"] == 401
    assert "abc123" not in payload["message"]
    assert "token=***" in payload["message"]


def test_429_error_returns_retry_metadata_when_retries_disabled(monkeypatch, tmp_path, capsys):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)
    monkeypatch.setenv("WB_API_TOKEN", "secret-token")

    def fake_urlopen(request, context=None, timeout=30):
        raise urllib.error.HTTPError(
            url=request.full_url,
            code=429,
            msg="Too Many Requests",
            hdrs={
                "X-Ratelimit-Retry": "2",
                "X-Ratelimit-Limit": "10",
                "X-Ratelimit-Reset": "29",
            },
            fp=io.BytesIO(b'{"detail":"slow down"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(SystemExit, match="1"):
        api_call.run_cli(
            [
                "--method",
                "GET",
                "--url",
                "https://common-api.wildberries.ru/ping",
                "--max-retries",
                "0",
            ]
        )

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == 429
    assert payload["rateLimit"] == {
        "retryAfterSeconds": "2",
        "burstLimit": "10",
        "resetAfterSeconds": "29",
    }


def test_script_entrypoint_invokes_run_cli():
    source = Path(api_call.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source
    assert "run_cli()" in source
