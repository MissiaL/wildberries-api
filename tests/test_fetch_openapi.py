import json
from pathlib import Path

from scripts import fetch_openapi


FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_category_pages_from_index():
    html = (FIXTURES / "swagger_index.html").read_text(encoding="utf-8")
    pages = fetch_openapi.extract_category_pages(html)
    assert pages == [
        "/en/docs/openapi/api-information",
        "/en/docs/openapi/work-with-products",
        "/en/docs/openapi/prices-and-discounts",
    ]


def test_extract_direct_schema_url():
    html = (FIXTURES / "swagger_direct.html").read_text(encoding="utf-8")
    assert (
        fetch_openapi.extract_schema_url(html)
        == "https://dev.wildberries.ru/static/openapi/content.json"
    )


def test_extract_embedded_schema_payload():
    html = (FIXTURES / "swagger_embedded.html").read_text(encoding="utf-8")
    payload = fetch_openapi.extract_embedded_schema(html)
    assert payload["openapi"] == "3.0.0"
    assert payload["info"]["title"] == "Analytics"


def test_extract_embedded_schema_payload_allows_brace_semicolon_in_string():
    html = """
    <html><body><script>
    window.__WB_EMBEDDED_OPENAPI__ = {"openapi":"3.0.0","info":{"title":"Analytics","example":"text }; more"},"servers":[{"url":"https://analytics-api.wildberries.ru"}]};
    </script></body></html>
    """
    payload = fetch_openapi.extract_embedded_schema(html)
    assert payload["info"]["example"] == "text }; more"


def test_parse_schema_document_supports_json():
    text = (FIXTURES / "direct_schema.json").read_text(encoding="utf-8")
    payload = fetch_openapi.parse_schema_document(text)
    assert payload["openapi"] == "3.0.0"
    assert payload["info"]["title"] == "Content"


def test_parse_schema_document_supports_yaml():
    text = (FIXTURES / "direct_schema.yaml").read_text(encoding="utf-8")
    payload = fetch_openapi.parse_schema_document(text)
    assert payload["openapi"] == "3.0.0"
    assert payload["info"]["title"] == "Content"


def test_build_manifest_records_servers_and_source(tmp_path):
    schema = {
        "openapi": "3.0.0",
        "info": {"title": "General"},
        "servers": [{"url": "https://common-api.wildberries.ru"}],
    }
    record = fetch_openapi.build_manifest_record(
        slug="general",
        doc_url="https://dev.wildberries.ru/en/docs/openapi/api-information",
        schema_filename="general.json",
        schema=schema,
        extraction_mode="embedded",
    )

    assert record["slug"] == "general"
    assert record["hosts"] == ["common-api.wildberries.ru"]
    assert record["schema_filename"] == "general.json"
    assert record["extraction_mode"] == "embedded"


def test_write_outputs_manifest_and_allowlist(tmp_path):
    records = [
        {
            "slug": "general",
            "hosts": ["common-api.wildberries.ru"],
            "schema_filename": "general.json",
        },
        {
            "slug": "content",
            "hosts": ["content-api.wildberries.ru"],
            "schema_filename": "content.json",
        },
    ]
    fetch_openapi.write_outputs(tmp_path, records)

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    allowlist = json.loads(
        (tmp_path / "host-allowlist.json").read_text(encoding="utf-8")
    )

    assert len(manifest["schemas"]) == 2
    assert allowlist["hosts"] == [
        "common-api.wildberries.ru",
        "content-api.wildberries.ru",
    ]
