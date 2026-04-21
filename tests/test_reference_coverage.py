from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
OPENAPI_DIR = ROOT / "assets" / "openapi"
REFERENCES_DIR = ROOT / "references"
REFERENCE_FILES = [
    "overview.md",
    "general.md",
    "content.md",
    "analytics.md",
    "prices-and-discounts.md",
    "marketplace.md",
    "supplies.md",
    "promotion.md",
    "feedbacks-and-questions.md",
    "statistics.md",
    "finance.md",
    "documents.md",
    "returns.md",
    "buyers-chat.md",
    "tariffs.md",
    "digital.md",
]


def test_reference_inventory_exists_and_is_non_empty():
    manifest = json.loads((OPENAPI_DIR / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schemas"], "expected fetched schema records in assets/openapi/manifest.json"

    for filename in REFERENCE_FILES:
        path = REFERENCES_DIR / filename
        assert path.exists(), f"missing reference file: {filename}"
        assert path.read_text(encoding="utf-8").strip(), f"reference file is empty: {filename}"


def test_overview_routes_every_manifest_slug_and_schema_filename():
    manifest = json.loads((OPENAPI_DIR / "manifest.json").read_text(encoding="utf-8"))
    overview = (REFERENCES_DIR / "overview.md").read_text(encoding="utf-8")

    for record in manifest["schemas"]:
        assert record["slug"] in overview, f"missing slug in overview routing: {record['slug']}"
        assert record["schema_filename"] in overview, (
            f"missing schema filename in overview routing: {record['schema_filename']}"
        )
