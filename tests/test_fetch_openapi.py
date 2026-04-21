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


def test_extract_openapi_pages_from_sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://dev.wildberries.ru/docs/openapi/api-information</loc>
        <lastmod>2026-04-20T13:02:56.000Z</lastmod>
      </url>
      <url>
        <loc>https://dev.wildberries.ru/swagger/api-information</loc>
        <lastmod>2026-04-20T13:02:56.000Z</lastmod>
      </url>
      <url>
        <loc>https://dev.wildberries.ru/docs/openapi/work-with-products</loc>
        <lastmod>2026-04-20T13:02:56.000Z</lastmod>
      </url>
    </urlset>
    """

    pages = fetch_openapi.extract_openapi_pages_from_sitemap(xml)

    assert pages == [
        {
            "slug": "api-information",
            "doc_url": "https://dev.wildberries.ru/en/docs/openapi/api-information",
            "swagger_url": "https://dev.wildberries.ru/en/swagger/general",
            "lastmod": "2026-04-20T13:02:56.000Z",
        },
        {
            "slug": "work-with-products",
            "doc_url": "https://dev.wildberries.ru/en/docs/openapi/work-with-products",
            "swagger_url": "https://dev.wildberries.ru/en/swagger/products",
            "lastmod": "2026-04-20T13:02:56.000Z",
        },
    ]


def test_extract_chapter_payload_from_swagger_html():
    html = r"""
    <script>
    self.__next_f.push([1,"{\"chapter\":\"Analytics\",\"path\":\"analytics\",\"groups\":[{\"title\":\"Reports\",\"tags\":[{\"title\":\"Get report\",\"path\":\"/api/v1/report\",\"method\":\"get\",\"tag\":\"Reports\"}]}]}"]);
    self.__next_f.push([1,"{\"chapter\":\"Documents\",\"path\":\"financial-reports-and-accounting\",\"groups\":[{\"title\":\"Documents\",\"tags\":[]}]}"]);
    </script>
    """

    payload = fetch_openapi.extract_chapter_payload(html, "analytics")

    assert payload["chapter"] == "Analytics"
    assert payload["path"] == "analytics"
    assert payload["groups"][0]["tags"][0]["path"] == "/api/v1/report"


def test_extract_operations_from_serialized_swagger_payload():
    html = r'''
    self.__next_f.push([1,"{\"title\":\"Create Product Cards\",\"path\":\"/content/v2/cards/upload\",\"method\":\"post\",\"tag\":\"Creating Product Cards\",\"key\":\"tag/Creating/paths/~1content~1v2~1cards~1upload/post\"}"]);
    '''

    operations = fetch_openapi.extract_operations_from_html(html)

    assert operations == [
        {
            "title": "Create Product Cards",
            "path": "/content/v2/cards/upload",
            "method": "post",
            "tag": "Creating Product Cards",
        }
    ]


def test_extract_operations_from_redoc_menu_html():
    html = """
    <span type="get" class="operation-type get">get</span>
    <span tabindex="0">Product Cards List{{ /content/v2/get/cards/list }}</span>
    """

    operations = fetch_openapi.extract_operations_from_html(html)

    assert operations == [
        {
            "title": "Product Cards List",
            "path": "/content/v2/get/cards/list",
            "method": "get",
            "tag": "Operations",
        }
    ]


def test_build_snapshot_schema_from_chapter_payload():
    chapter = {
        "chapter": "Analytics",
        "path": "analytics",
        "groups": [
            {
                "title": "Reports",
                "tags": [
                    {
                        "title": "Get report",
                        "path": "/api/v1/report",
                        "method": "get",
                        "tag": "Reports",
                    }
                ],
            }
        ],
    }

    schema = fetch_openapi.build_snapshot_schema(
        slug="analytics",
        doc_url="https://dev.wildberries.ru/en/docs/openapi/analytics",
        swagger_url="https://dev.wildberries.ru/en/swagger/analytics",
        chapter=chapter,
        hosts=["seller-analytics-api.wildberries.ru"],
    )

    assert schema["openapi"] == "3.0.0"
    assert schema["info"]["title"] == "Analytics"
    assert schema["servers"] == [{"url": "https://seller-analytics-api.wildberries.ru"}]
    assert schema["paths"]["/api/v1/report"]["get"]["summary"] == "Get report"
    assert schema["paths"]["/api/v1/report"]["get"]["tags"] == ["Reports"]


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
            "schema": {"openapi": "3.0.0", "info": {"title": "General"}, "servers": []},
        },
        {
            "slug": "content",
            "hosts": ["content-api.wildberries.ru"],
            "schema_filename": "content.json",
            "schema": {"openapi": "3.0.0", "info": {"title": "Content"}, "servers": []},
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
    assert (
        json.loads((tmp_path / "general.json").read_text(encoding="utf-8"))["info"]["title"]
        == "General"
    )
    assert (
        json.loads((tmp_path / "content.json").read_text(encoding="utf-8"))["info"]["title"]
        == "Content"
    )


def test_write_outputs_handles_empty_records(tmp_path):
    fetch_openapi.write_outputs(tmp_path, [])

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    allowlist = json.loads(
        (tmp_path / "host-allowlist.json").read_text(encoding="utf-8")
    )

    assert manifest == {"schemas": []}
    assert allowlist == {"hosts": []}
