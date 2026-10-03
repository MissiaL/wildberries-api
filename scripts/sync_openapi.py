"""Install official Wildberries OpenAPI specs and extract documented limits.

Accepts a JSON export keyed by documentation slug or downloaded specifications
from ``fetch_openapi.py``. Derives per-operation limits from official
``description_limit`` blocks and records genuinely absent limits explicitly.
"""

from argparse import ArgumentParser
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import urllib.parse


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_DIR = ROOT / "assets" / "openapi"
MANIFEST_PATH = OPENAPI_DIR / "manifest.json"
RATE_LIMIT_MANIFEST_PATH = OPENAPI_DIR / "rate-limit-manifest.json"
METHODS = {"get", "post", "put", "patch", "delete"}
LIMIT_BLOCK_RE = re.compile(
    r'<div class=["\']description_limit["\']>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
HTML_TAG_RE = re.compile(r"<[^>]+>")
HEADER_NAMES = {
    "type": "type",
    "period": "period",
    "limit": "limit",
    "interval": "interval",
    "burst": "burst",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def clean_text(value):
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = HTML_TAG_RE.sub(" ", value)
    value = html.unescape(value)
    return "\n".join(
        line for raw in value.splitlines() if (line := " ".join(raw.split()))
    )


def split_markdown_row(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_rate_limit(description, source, captured_at):
    match = LIMIT_BLOCK_RE.search(description or "")
    if not match:
        raise ValueError("operation has no description_limit block")

    block = match.group(1)
    lines = [line.strip() for line in block.splitlines()]
    header_index = None
    headers = None
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        candidate = split_markdown_row(line)
        lowered = {cell.lower() for cell in candidate}
        if {"period", "limit", "interval", "burst"}.issubset(lowered):
            header_index = index
            headers = candidate
            break

    if header_index is None:
        return {
            "scope": "Non-tabular limit from the official operation description",
            "raw": clean_text(block),
            "source": source,
            "verifiedAt": captured_at,
        }

    row_index = header_index + 2
    rows = []
    while row_index < len(lines) and lines[row_index].startswith("|"):
        values = split_markdown_row(lines[row_index])
        rows.append(
            {
                HEADER_NAMES.get(header.lower(), header): values[index]
                if index < len(values)
                else None
                for index, header in enumerate(headers)
            }
        )
        row_index += 1

    scope = clean_text("\n".join(lines[:header_index]))
    note = clean_text("\n".join(lines[row_index:]))
    payload = {
        "scope": scope,
        "limits": rows,
        "source": source,
        "verifiedAt": captured_at,
    }
    if note:
        payload["note"] = note
    return payload


def operation_source(slug, operation):
    tag = (operation.get("tags") or ["Operations"])[0]
    operation_id = operation.get("operationId")
    base = f"https://dev.wildberries.ru/docs/openapi/{slug}"
    if operation_id:
        return f"{base}#tag/{tag}/operation/{operation_id}"
    return base


def operation_count(schema):
    return sum(
        1
        for path_item in schema.get("paths", {}).values()
        for method in path_item
        if method.lower() in METHODS
    )


def path_count(schema):
    return sum(
        1
        for path_item in schema.get("paths", {}).values()
        if any(method.lower() in METHODS for method in path_item)
    )


def preserve_key_order(value, previous):
    if isinstance(value, dict) and isinstance(previous, dict):
        return {key: preserve_key_order(value[key], previous.get(key))
                for key in dict.fromkeys([*previous, *value]) if key in value}
    if isinstance(value, list) and isinstance(previous, list):
        return [preserve_key_order(item, previous[index] if index < len(previous) else None)
                for index, item in enumerate(value)]
    return value


def extract_hosts(schema):
    nodes = [schema]
    for path_item in schema.get("paths", {}).values():
        nodes.append(path_item)
        nodes.extend(operation for method, operation in path_item.items() if method.lower() in METHODS)
    hosts = set()
    for node in nodes:
        for server in node.get("servers", []):
            url = urllib.parse.urlparse(server.get("url", ""))
            host = url.hostname or ""
            if (url.scheme == "https" and host.endswith("-api.wildberries.ru")
                    and "sandbox" not in host and url.port in (None, 443)
                    and url.username is None and url.password is None):
                hosts.add(host)
    return sorted(hosts)


def sync(export_path, captured_at=None, output_dir=None):
    live_specs = export_path if isinstance(export_path, dict) else load_json(export_path)
    openapi_dir = Path(output_dir) if output_dir else OPENAPI_DIR
    manifest_path = openapi_dir / "manifest.json"
    manifest = load_json(manifest_path)
    expected_slugs = [record["slug"] for record in manifest["schemas"]]
    if set(live_specs) != set(expected_slugs):
        raise ValueError(
            f"live export slugs differ from manifest: live={sorted(live_specs)} "
            f"manifest={sorted(expected_slugs)}"
        )

    captured_at = captured_at or datetime.now(timezone.utc).isoformat()
    total_operations = 0
    total_special = 0
    undocumented = []
    output_schemas = {}

    for record in manifest["schemas"]:
        slug = record["slug"]
        schema = live_specs[slug]
        source_url = record.get("schema_source_url")
        mode = "direct-schema-url" if source_url else "browser-redoc-openapi"
        for path, path_item in schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.lower() not in METHODS:
                    continue
                source = operation_source(slug, operation)
                try:
                    rate_limit = parse_rate_limit(
                        operation.get("description", ""), source, captured_at
                    )
                except ValueError:
                    if LIMIT_BLOCK_RE.search(operation.get("description", "")):
                        raise
                    rate_limit = {
                        "status": "undocumented",
                        "source": source,
                        "verifiedAt": captured_at,
                        "note": "The current official operation publishes no rate limit; verify with WB before repeated calls.",
                    }
                    undocumented.append({"slug": slug, "method": method.upper(), "path": path})
                operation["x-wb-rate-limits"] = rate_limit
                if "raw" in rate_limit:
                    total_special += 1

        count = operation_count(schema)
        total_operations += count
        schema["x-wb-extraction"] = {
            "mode": mode,
            "doc_url": record["doc_url"],
            "capturedAt": captured_at,
        }
        if source_url:
            schema["x-wb-extraction"]["schema_source_url"] = source_url
        schema["x-wb-rate-limits"] = {
            "verifiedAt": captured_at,
            "source": record["doc_url"],
            "operationCount": count,
        }
        if slug == "api-information":
            introduction = next(
                (tag for tag in schema.get("tags", []) if tag.get("name", "").lower() == "introduction"),
                {},
            )
            if LIMIT_BLOCK_RE.search(introduction.get("description", "")):
                schema["x-wb-category-rate-limit-example"] = parse_rate_limit(
                    introduction["description"],
                    f"{record['doc_url']}#tag/introduction/Rate-Limits",
                    captured_at,
                )

        record["title"] = schema.get("info", {}).get("title", record["title"])
        record["hosts"] = extract_hosts(schema)
        record["extraction_mode"] = mode
        record["path_count"] = path_count(schema)
        record["operation_count"] = count
        record["fetched_at"] = captured_at
        record["rate_limits_verified_at"] = captured_at
        output_schemas[record["schema_filename"]] = schema

    for filename, schema in output_schemas.items():
        destination = openapi_dir / filename
        # Keep unchanged JSON keys in place so refresh diffs show schema changes.
        if destination.exists():
            schema = preserve_key_order(schema, load_json(destination))
        write_json(destination, schema)
    write_json(manifest_path, manifest)
    write_json(openapi_dir / "host-allowlist.json", {
        "hosts": sorted({host for record in manifest["schemas"] for host in record["hosts"]}),
    })
    write_json(
        openapi_dir / "rate-limit-manifest.json",
        {
            "schemaVersion": 2,
            "verifiedAt": captured_at,
            "source": "Official Wildberries OpenAPI specifications",
            "operationCount": total_operations,
            "documentedLimitCount": total_operations - len(undocumented),
            "undocumentedLimits": undocumented,
            "specialLimitCount": total_special,
            "pages": [
                {
                    "slug": record["slug"],
                    "operationCount": record["operation_count"],
                }
                for record in manifest["schemas"]
            ],
        },
    )


def main():
    parser = ArgumentParser()
    parser.add_argument("export", help="JSON object keyed by WB documentation slug")
    parser.add_argument(
        "--captured-at",
        help="ISO timestamp from the browser capture (defaults to current UTC time)",
    )
    args = parser.parse_args()
    sync(args.export, captured_at=args.captured_at)


if __name__ == "__main__":
    main()
