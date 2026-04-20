import json
import re

import yaml


CATEGORY_LINK_RE = re.compile(r'href="(/en/docs/openapi/[^"#?]+)"')
SPEC_URL_RE = re.compile(r'spec-url="([^"]+)"')
EMBEDDED_RE = re.compile(
    r"window\.__WB_EMBEDDED_OPENAPI__\s*=\s*(\{.*?\});",
    re.DOTALL,
)


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
    match = EMBEDDED_RE.search(html)
    if not match:
        return None
    return json.loads(match.group(1))


def parse_schema_document(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)
