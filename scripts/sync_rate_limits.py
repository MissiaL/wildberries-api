"""Merge rate limits extracted from live WB OpenAPI pages into local snapshots.

The live export is produced in a real browser because dev.wildberries.ru
returns HTTP 498 to plain HTTP clients. Each export record must be tied to an
exact page, method, and path. This script intentionally fails if any resulting
operation lacks a rate-limit block.
"""

from argparse import ArgumentParser
import json
from pathlib import Path
import urllib.parse


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_DIR = ROOT / "assets" / "openapi"
MANIFEST_PATH = OPENAPI_DIR / "manifest.json"
RATE_LIMIT_MANIFEST_PATH = OPENAPI_DIR / "rate-limit-manifest.json"
METHODS = {"get", "post", "put", "patch", "delete"}
REMOVED_OPERATIONS = {
    ("reports", "get", "/api/v1/supplier/stocks"),
    (
        "financial-reports-and-accounting",
        "get",
        "/api/v5/supplier/reportDetailByPeriod",
    ),
    ("promotion", "post", "/api/content/v1/recommendations/list"),
    ("promotion", "post", "/api/content/v1/recommendations/set"),
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_rate_limit(record, captured_at):
    payload = {
        "scope": record.get("scope"),
        "limits": record["limits"],
        "source": record["sourceAnchor"],
        "verifiedAt": captured_at,
    }
    if record.get("note"):
        payload["note"] = record["note"]
    return payload


def build_special_rate_limit(record, captured_at):
    return {
        "scope": "Non-tabular limit from the official operation description",
        "raw": record["text"],
        "source": f"{record['sourceUrl']}#{record['sectionId']}",
        "verifiedAt": captured_at,
    }


def build_operation(record, rate_limit):
    host = urllib.parse.urlparse(record.get("url") or "").hostname
    description = f"See {record['sourceAnchor']} for current request and response details."
    operation = {
        "summary": record.get("title") or f"{record['method']} {record['path']}",
        "tags": ["Live documentation"],
        "operationId": record["sectionId"],
        "description": description,
        "responses": {
            "200": {
                "description": "Operation details are documented on the official Wildberries page."
            }
        },
        "x-wb-group": "Live documentation",
        "x-wb-rate-limits": rate_limit,
    }
    if host:
        operation["x-wb-host"] = host
    return operation


def operation_count(schema):
    return sum(
        1
        for operations in schema.get("paths", {}).values()
        for method in operations
        if method.lower() in METHODS
    )


def sync(export_path):
    export = load_json(export_path)
    captured_at = export["capturedAt"]
    manifest = load_json(MANIFEST_PATH)
    records = [
        record
        for record in export["records"]
        if record.get("page") and record.get("method") and record.get("path")
    ]
    standard = {
        (record["page"], record["method"].lower(), record["path"]): record
        for record in records
    }
    special = {
        (record["page"], record["method"].lower(), record["path"]): record
        for record in export.get("specialLimits", [])
    }
    if len(standard) + len(special) != export["operationCount"]:
        raise ValueError("duplicate or incomplete live rate-limit records")

    schemas = {}
    missing = []
    for manifest_record in manifest["schemas"]:
        slug = manifest_record["slug"]
        schema_path = OPENAPI_DIR / manifest_record["schema_filename"]
        schema = load_json(schema_path)

        for removed_slug, method, path in REMOVED_OPERATIONS:
            if slug != removed_slug or path not in schema.get("paths", {}):
                continue
            schema["paths"][path].pop(method, None)
            if not schema["paths"][path]:
                del schema["paths"][path]

        page_records = {
            key: record for key, record in standard.items() if key[0] == slug
        }
        page_special = {
            key: record for key, record in special.items() if key[0] == slug
        }
        for (_, method, path), record in page_records.items():
            rate_limit = build_rate_limit(record, captured_at)
            operation = schema.setdefault("paths", {}).setdefault(path, {}).get(method)
            if operation is None:
                operation = build_operation(record, rate_limit)
                schema["paths"][path][method] = operation
            else:
                operation["x-wb-rate-limits"] = rate_limit

        for (_, method, path), record in page_special.items():
            rate_limit = build_special_rate_limit(record, captured_at)
            operation = schema.setdefault("paths", {}).setdefault(path, {}).get(method)
            if operation is None:
                operation = build_operation(
                    {
                        **record,
                        "sourceAnchor": f"{record['sourceUrl']}#{record['sectionId']}",
                        "url": None,
                    },
                    rate_limit,
                )
                schema["paths"][path][method] = operation
            else:
                operation["x-wb-rate-limits"] = rate_limit

        for path, operations in schema.get("paths", {}).items():
            for method, operation in operations.items():
                if method.lower() not in METHODS:
                    continue
                if "x-wb-rate-limits" not in operation:
                    missing.append(f"{slug}: {method.upper()} {path}")

        schema["x-wb-rate-limits"] = {
            "verifiedAt": captured_at,
            "source": manifest_record["doc_url"],
            "operationCount": operation_count(schema),
        }
        if slug == "api-information":
            category_example = next(
                record
                for record in export["records"]
                if record.get("sectionId") == "tag/introduction/Limity-zaprosov"
            )
            schema["x-wb-category-rate-limit-example"] = build_rate_limit(
                category_example,
                captured_at,
            )

        schemas[slug] = (schema_path, schema)
        manifest_record["path_count"] = len(schema.get("paths", {}))
        manifest_record["operation_count"] = operation_count(schema)
        manifest_record["rate_limits_verified_at"] = captured_at

    if missing:
        raise ValueError("operations without live rate limits:\n" + "\n".join(missing))

    for schema_path, schema in schemas.values():
        write_json(schema_path, schema)
    write_json(MANIFEST_PATH, manifest)
    write_json(
        RATE_LIMIT_MANIFEST_PATH,
        {
            "schemaVersion": export["schemaVersion"],
            "verifiedAt": captured_at,
            "source": export["source"],
            "operationCount": sum(operation_count(schema) for _, schema in schemas.values()),
            "pages": [
                {
                    "slug": slug,
                    "operationCount": operation_count(schema),
                }
                for slug, (_, schema) in schemas.items()
            ],
        },
    )


def main():
    parser = ArgumentParser()
    parser.add_argument("export", help="JSON export extracted from the live WB OpenAPI pages")
    args = parser.parse_args()
    sync(args.export)


if __name__ == "__main__":
    main()
