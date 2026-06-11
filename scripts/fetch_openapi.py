"""Fetch Wildberries OpenAPI doc snapshots from dev.wildberries.ru.

NOTE (2026-06): dev.wildberries.ru sits behind an anti-bot challenge and
returns HTTP 498 for plain urllib/curl requests, so running this script
directly fails. Workaround: open the docs in a real browser session
(Playwright/Chrome), extract the per-chapter payloads from the page HTML
(same logic as extract_chapter_payload), then rebuild the snapshots offline
with build_snapshot_schema / build_manifest_record / write_outputs.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assets" / "openapi"
SITEMAP_URL = "https://dev.wildberries.ru/sitemap.xml"
DOCS_BASE_URL = "https://dev.wildberries.ru/en/docs/openapi"
SWAGGER_BASE_URL = "https://dev.wildberries.ru/en/swagger"
CATEGORY_LINK_RE = re.compile(r'href="(/en/docs/openapi/[^"#?]+)"')
SPEC_URL_RE = re.compile(r'spec-url="([^"]+)"')
EMBEDDED_ASSIGNMENT = "window.__WB_EMBEDDED_OPENAPI__"
HOST_URL_RE = re.compile(r"https://([a-z0-9.-]+\.wildberries\.ru)(?:/[^\s\"'<>]*)?")
SERIALIZED_OPERATION_RE = re.compile(
    r'\{"title":"(?P<title>[^"]+)","path":"(?P<path>/[^"]+)",'
    r'"method":"(?P<method>get|post|put|patch|delete)","tag":"(?P<tag>[^"]+)"',
)
REDOC_MENU_OPERATION_RE = re.compile(
    r'<span type="(?P<method>get|post|put|patch|delete)"[^>]*>.*?</span>'
    r'\s*<span[^>]*>(?P<title>.*?)\{\{ (?P<path>/[^}]+) \}\}</span>',
    re.DOTALL,
)
HTML_TAG_RE = re.compile(r"<[^>]+>")
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
REQUEST_HEADERS = {
    "User-Agent": "wildberries-api-skill/1.0 (+https://dev.wildberries.ru)",
    "Accept-Language": "en",
}
PRODUCTION_API_HOSTS = {
    "common-api.wildberries.ru",
    "user-management-api.wildberries.ru",
    "content-api.wildberries.ru",
    "seller-analytics-api.wildberries.ru",
    "discounts-prices-api.wildberries.ru",
    "marketplace-api.wildberries.ru",
    "statistics-api.wildberries.ru",
    "advert-api.wildberries.ru",
    "feedbacks-api.wildberries.ru",
    "buyer-chat-api.wildberries.ru",
    "supplies-api.wildberries.ru",
    "returns-api.wildberries.ru",
    "documents-api.wildberries.ru",
    "finance-api.wildberries.ru",
}
SWAGGER_SLUG_ALIASES = {
    "api-information": "general",
    "financial-reports-and-accounting": "finances",
    "user-communication": "communications",
    "wb-tariffs": "tariffs",
    "work-with-products": "products",
}
HOST_FALLBACKS_BY_DOC_SLUG = {
    "api-information": [
        "common-api.wildberries.ru",
        "user-management-api.wildberries.ru",
    ],
    "work-with-products": ["content-api.wildberries.ru"],
    "orders-fbs": ["marketplace-api.wildberries.ru"],
    "orders-dbw": ["marketplace-api.wildberries.ru"],
    "orders-dbs": ["marketplace-api.wildberries.ru"],
    "in-store-pickup": ["marketplace-api.wildberries.ru"],
    "orders-fbw": ["supplies-api.wildberries.ru"],
    "promotion": ["advert-api.wildberries.ru"],
    "user-communication": [
        "feedbacks-api.wildberries.ru",
        "buyer-chat-api.wildberries.ru",
        "returns-api.wildberries.ru",
    ],
    "wb-tariffs": ["common-api.wildberries.ru"],
    "analytics": ["seller-analytics-api.wildberries.ru"],
    "reports": ["statistics-api.wildberries.ru"],
    "financial-reports-and-accounting": [
        "documents-api.wildberries.ru",
        "finance-api.wildberries.ru",
    ],
}


def extract_category_pages(html):
    seen = []
    for match in CATEGORY_LINK_RE.findall(html):
        if match not in seen:
            seen.append(match)
    return seen


def extract_schema_url(html):
    match = SPEC_URL_RE.search(html)
    return match.group(1) if match else None


def extract_embedded_schema(html):
    start = html.find(EMBEDDED_ASSIGNMENT)
    if start == -1:
        return None
    start = html.find("=", start)
    if start == -1:
        return None
    start = html.find("{", start)
    if start == -1:
        return None
    payload, _ = json.JSONDecoder().raw_decode(html[start:])
    return payload


def parse_schema_document(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)


def fetch_text(url):
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(
        request,
        context=ssl.create_default_context(),
        timeout=60,
    ) as response:
        return response.read().decode("utf-8", errors="replace")


def swagger_slug_for(doc_slug):
    return SWAGGER_SLUG_ALIASES.get(doc_slug, doc_slug)


def extract_openapi_pages_from_sitemap(xml_text):
    root = ET.fromstring(xml_text)
    pages = []
    for entry in root.findall("sm:url", SITEMAP_NS):
        loc = entry.findtext("sm:loc", namespaces=SITEMAP_NS)
        if not loc:
            continue
        parsed = urllib.parse.urlparse(loc)
        if not parsed.path.startswith("/docs/openapi/"):
            continue
        slug = parsed.path.rsplit("/", 1)[-1]
        pages.append(
            {
                "slug": slug,
                "doc_url": f"{DOCS_BASE_URL}/{slug}",
                "swagger_url": f"{SWAGGER_BASE_URL}/{swagger_slug_for(slug)}",
                "lastmod": entry.findtext("sm:lastmod", default="", namespaces=SITEMAP_NS),
            }
        )
    return pages


def normalize_swagger_payload(html):
    return (
        html.replace('\\"', '"')
        .replace("\\u0026", "&")
        .replace("\\u003c", "<")
        .replace("\\u003e", ">")
    )


def extract_chapter_payload(html, slug):
    normalized = normalize_swagger_payload(html)
    decoder = json.JSONDecoder()
    marker = f'"path":"{slug}"'
    search_from = 0

    while True:
        path_index = normalized.find(marker, search_from)
        if path_index == -1:
            return None
        start = normalized.rfind('{"chapter":"', 0, path_index)
        if start == -1:
            search_from = path_index + len(marker)
            continue
        try:
            payload, _ = decoder.raw_decode(normalized[start:])
        except json.JSONDecodeError:
            search_from = path_index + len(marker)
            continue
        if payload.get("path") == slug and isinstance(payload.get("groups"), list):
            return payload
        search_from = path_index + len(marker)


def slug_to_title(slug):
    return slug.replace("-", " ").title()


def clean_html_text(value):
    value = HTML_TAG_RE.sub("", value)
    return " ".join(value.split())


def extract_operations_from_html(html):
    normalized = normalize_swagger_payload(html)
    operations = []
    seen = set()

    for match in SERIALIZED_OPERATION_RE.finditer(normalized):
        operation = {
            "title": match.group("title"),
            "path": match.group("path"),
            "method": match.group("method"),
            "tag": match.group("tag"),
        }
        key = (operation["method"], operation["path"], operation["title"])
        if key not in seen:
            operations.append(operation)
            seen.add(key)

    for match in REDOC_MENU_OPERATION_RE.finditer(normalized):
        operation = {
            "title": clean_html_text(match.group("title")),
            "path": match.group("path"),
            "method": match.group("method"),
            "tag": "Operations",
        }
        key = (operation["method"], operation["path"], operation["title"])
        if key not in seen:
            operations.append(operation)
            seen.add(key)

    return operations


def build_chapter_from_operations(slug, html):
    operations = extract_operations_from_html(html)
    groups_by_tag = {}
    for operation in operations:
        groups_by_tag.setdefault(operation.get("tag") or "Operations", []).append(operation)

    return {
        "chapter": slug_to_title(slug),
        "path": slug,
        "groups": [
            {"title": tag, "tags": tag_operations}
            for tag, tag_operations in groups_by_tag.items()
        ],
    }


def build_operation_id(method, path):
    cleaned = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", cleaned).strip("_")
    return f"{method.lower()}_{cleaned or 'root'}"


def build_snapshot_schema(slug, doc_url, swagger_url, chapter, hosts):
    title = chapter.get("chapter") or slug_to_title(slug)
    description = (
        "Production documentation snapshot extracted from the official Wildberries "
        f"documentation HTML for {doc_url} and {swagger_url}."
    )
    tags = []
    seen_tag_names = set()
    paths = {}
    operation_count = 0

    for group in chapter.get("groups", []):
        group_title = group.get("title") or title
        if group_title not in seen_tag_names:
            tags.append({"name": group_title})
            seen_tag_names.add(group_title)

        for operation in group.get("tags", []):
            path = operation.get("path")
            method = str(operation.get("method", "")).lower()
            if not path or not method:
                continue
            operation_tag = operation.get("tag") or group_title
            if operation_tag not in seen_tag_names:
                tags.append({"name": operation_tag})
                seen_tag_names.add(operation_tag)
            operation_schema = {
                "summary": operation.get("title") or f"{method.upper()} {path}",
                "tags": [operation_tag],
                "operationId": operation.get("key") or build_operation_id(method, path),
                "description": f"See {doc_url} and {swagger_url} for request and response details.",
                "responses": {
                    "200": {
                        "description": "Operation details are documented on the official Wildberries page."
                    }
                },
                "x-wb-group": group_title,
            }
            if operation.get("isDeprecated"):
                operation_schema["deprecated"] = True
            paths.setdefault(path, {})[method] = operation_schema
            operation_count += 1

    return {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": "html-snapshot",
            "description": description,
        },
        "servers": [{"url": f"https://{host}"} for host in hosts],
        "tags": tags,
        "paths": paths,
        "x-wb-extraction": {
            "mode": "docs-html-snapshot",
            "doc_url": doc_url,
            "swagger_url": swagger_url,
            "chapter_path": chapter.get("path") or slug,
            "group_count": len(chapter.get("groups", [])),
            "operation_count": operation_count,
        },
    }


def extract_hosts(schema):
    hosts = []
    for server in schema.get("servers", []):
        hostname = urllib.parse.urlparse(server["url"]).hostname
        if hostname and hostname not in hosts and "sandbox" not in hostname:
            hosts.append(hostname)
    return hosts


def extract_hosts_from_text(*texts):
    hosts = []
    for text in texts:
        for host in HOST_URL_RE.findall(text):
            if host in PRODUCTION_API_HOSTS and host not in hosts:
                hosts.append(host)
    return hosts


def build_manifest_record(
    slug,
    doc_url,
    schema_filename,
    schema,
    extraction_mode,
    schema_source_url=None,
    swagger_url=None,
    source_lastmod=None,
):
    return {
        "slug": slug,
        "title": schema.get("info", {}).get("title", slug),
        "doc_url": doc_url,
        "swagger_url": swagger_url,
        "schema_source_url": schema_source_url,
        "schema_filename": schema_filename,
        "hosts": extract_hosts(schema),
        "extraction_mode": extraction_mode,
        "path_count": len(schema.get("paths", {})),
        "operation_count": sum(len(methods) for methods in schema.get("paths", {}).values()),
        "source_lastmod": source_lastmod,
        "provenance": {
            "sitemap_url": SITEMAP_URL,
            "doc_url": doc_url,
            "swagger_url": swagger_url,
            "schema_source_url": schema_source_url,
            "source_lastmod": source_lastmod,
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def write_outputs(output_dir, records):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_records = []
    hosts = []
    for record in records:
        schema = record.get("schema")
        if schema:
            (output_dir / record["schema_filename"]).write_text(
                json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        manifest_records.append({key: value for key, value in record.items() if key != "schema"})
        for host in record.get("hosts", []):
            if host not in hosts:
                hosts.append(host)

    (output_dir / "manifest.json").write_text(
        json.dumps({"schemas": manifest_records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "host-allowlist.json").write_text(
        json.dumps({"hosts": sorted(hosts)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def fetch_page_schema(page):
    doc_html = fetch_text(page["doc_url"])
    swagger_html = fetch_text(page["swagger_url"])

    schema_source_url = extract_schema_url(swagger_html) or extract_schema_url(doc_html)
    if schema_source_url:
        schema = parse_schema_document(fetch_text(schema_source_url))
        extraction_mode = "direct-schema-url"
    else:
        embedded_schema = extract_embedded_schema(swagger_html) or extract_embedded_schema(doc_html)
        if embedded_schema:
            schema = embedded_schema
            extraction_mode = "embedded-openapi"
        else:
            chapter = (
                extract_chapter_payload(swagger_html, page["slug"])
                or extract_chapter_payload(doc_html, page["slug"])
                or build_chapter_from_operations(page["slug"], swagger_html)
                or {"chapter": slug_to_title(page["slug"]), "path": page["slug"], "groups": []}
            )
            hosts = extract_hosts_from_text(doc_html, swagger_html) or HOST_FALLBACKS_BY_DOC_SLUG.get(
                page["slug"],
                [],
            )
            schema = build_snapshot_schema(
                slug=page["slug"],
                doc_url=page["doc_url"],
                swagger_url=page["swagger_url"],
                chapter=chapter,
                hosts=hosts,
            )
            extraction_mode = "docs-html-snapshot"

    schema_filename = f"{page['slug']}.json"
    record = build_manifest_record(
        slug=page["slug"],
        doc_url=page["doc_url"],
        swagger_url=page["swagger_url"],
        schema_filename=schema_filename,
        schema=schema,
        extraction_mode=extraction_mode,
        schema_source_url=schema_source_url,
        source_lastmod=page.get("lastmod"),
    )
    record["schema"] = schema
    return record


def fetch_all(output_dir=OUTPUT_DIR):
    sitemap = fetch_text(SITEMAP_URL)
    pages = extract_openapi_pages_from_sitemap(sitemap)
    records = [fetch_page_schema(page) for page in pages]
    write_outputs(output_dir, records)
    return records


def main():
    fetch_all()


if __name__ == "__main__":
    main()
