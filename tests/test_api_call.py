import json

import pytest

from scripts import api_call


def test_validate_url_rejects_non_allowlisted_host(tmp_path, monkeypatch):
    allowlist = tmp_path / "host-allowlist.json"
    allowlist.write_text(json.dumps({"hosts": ["common-api.wildberries.ru"]}), encoding="utf-8")
    monkeypatch.setattr(api_call, "ALLOWLIST_PATH", allowlist)

    with pytest.raises(ValueError, match="Blocked host"):
        api_call.validate_url("https://evil.example.com/api/v1/data")


def test_filter_headers_blocks_sensitive_headers():
    with pytest.raises(ValueError, match="Blocked headers"):
        api_call.filter_headers({"Authorization": "abc"})


def test_get_token_fails_when_env_missing(monkeypatch):
    monkeypatch.delenv("WB_API_TOKEN", raising=False)

    with pytest.raises(ValueError, match="WB_API_TOKEN"):
        api_call.get_token()
