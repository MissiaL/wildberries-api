import io
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

import pytest

from scripts import api_call


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


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
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
        hdrs=None,
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


def test_script_entrypoint_invokes_run_cli():
    source = Path(api_call.__file__).read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source
    assert "run_cli()" in source
