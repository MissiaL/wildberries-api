from scripts.sync_openapi import parse_rate_limit


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
