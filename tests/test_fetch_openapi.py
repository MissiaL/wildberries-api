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


def test_parse_schema_document_supports_yaml():
    text = (FIXTURES / "direct_schema.yaml").read_text(encoding="utf-8")
    payload = fetch_openapi.parse_schema_document(text)
    assert payload["openapi"] == "3.0.0"
    assert payload["info"]["title"] == "Content"
