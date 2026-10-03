import json

import pytest

from scripts import sync_openapi
from scripts.sync_openapi import parse_rate_limit, sync


def test_parse_tabular_rate_limit_uses_stable_keys():
    description = """
<div class="description_limit">
Request limit per seller account:

| Type | Period | Limit | Interval | Burst |
| --- | --- | --- | --- | --- |
| Personal | 1 min | 1 request | 1 min | 10 requests |

One 4XX response counts as 10 requests
</div>
"""

    result = parse_rate_limit(description, "https://example.test", "2026-08-19T00:00:00Z")

    assert result["limits"] == [
        {
            "type": "Personal",
            "period": "1 min",
            "limit": "1 request",
            "interval": "1 min",
            "burst": "10 requests",
        }
    ]
    assert result["note"] == "One 4XX response counts as 10 requests"


def test_parse_non_tabular_rate_limit():
    result = parse_rate_limit(
        '<div class="description_limit">Maximum 3 requests per 30 seconds.</div>',
        "https://example.test",
        "2026-08-19T00:00:00Z",
    )

    assert result["raw"] == "Maximum 3 requests per 30 seconds."


def test_sync_replaces_stale_limits_with_explicit_missing_status(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({"schemas": [{
        "slug": "reports", "title": "Reports", "schema_filename": "reports.json",
        "doc_url": "https://dev.wildberries.ru/en/docs/openapi/reports",
        "schema_source_url": "https://dev.wildberries.ru/api/swagger/yaml/en/12-reports.yaml",
    }]}))
    sync({"reports": {"openapi": "3.0.1", "paths": {"/returns": {"get": {
        "description": "Returns a list.", "x-wb-rate-limits": {"limits": [{"limit": "10"}]},
    }}}}}, captured_at="2026-10-03T00:00:00Z", output_dir=tmp_path)

    schema = json.loads((tmp_path / "reports.json").read_text())
    limit = schema["paths"]["/returns"]["get"]["x-wb-rate-limits"]
    assert limit["status"] == "undocumented"
    assert "limits" not in limit
    assert schema["x-wb-extraction"]["mode"] == "direct-schema-url"
    manifest = json.loads((tmp_path / "rate-limit-manifest.json").read_text())
    assert manifest["documentedLimitCount"] == 0
    assert manifest["undocumentedLimits"] == [{"slug": "reports", "method": "GET", "path": "/returns"}]


def test_sync_propagates_parse_failure_when_limit_block_exists(tmp_path, monkeypatch):
    (tmp_path / "manifest.json").write_text(json.dumps({"schemas": [{
        "slug": "reports", "title": "Reports", "schema_filename": "reports.json",
        "doc_url": "https://dev.wildberries.ru/en/docs/openapi/reports",
    }]}))

    def fail_to_parse(*args):
        raise ValueError("unsupported official limit format")

    monkeypatch.setattr(sync_openapi, "parse_rate_limit", fail_to_parse)
    with pytest.raises(ValueError, match="unsupported official limit format"):
        sync({"reports": {"paths": {"/returns": {"get": {
            "description": '<div class="description_limit">Present limit.</div>',
        }}}}}, output_dir=tmp_path)
    assert not (tmp_path / "reports.json").exists()
