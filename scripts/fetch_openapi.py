from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.parse

import yaml


CATEGORY_LINK_RE = re.compile(r'href="(/en/docs/openapi/[^"#?]+)"')
SPEC_URL_RE = re.compile(r'spec-url="([^"]+)"')
EMBEDDED_ASSIGNMENT = "window.__WB_EMBEDDED_OPENAPI__"


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


def extract_hosts(schema):
    hosts = []
    for server in schema.get("servers", []):
        hostname = urllib.parse.urlparse(server["url"]).hostname
        if hostname and hostname not in hosts and "sandbox" not in hostname:
            hosts.append(hostname)
    return hosts


def build_manifest_record(
    slug,
    doc_url,
    schema_filename,
    schema,
    extraction_mode,
    schema_source_url=None,
):
    return {
        "slug": slug,
        "title": schema.get("info", {}).get("title", slug),
        "doc_url": doc_url,
        "schema_source_url": schema_source_url,
        "schema_filename": schema_filename,
        "hosts": extract_hosts(schema),
        "extraction_mode": extraction_mode,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def write_outputs(output_dir, records):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"schemas": records}
    hosts = sorted({host for record in records for host in record["hosts"]})
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "host-allowlist.json").write_text(
        json.dumps({"hosts": hosts}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
