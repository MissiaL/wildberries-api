from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def test_public_skill_scaffold_exists():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["name"] == "wildberries-api"
    assert "SKILL.md" in package["files"]
    assert (ROOT / "scripts").is_dir()
    assert (ROOT / "references").is_dir()
    assert (ROOT / "assets" / "openapi").is_dir()


def test_skill_and_readme_explain_runtime_contract():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "name: wildberries-api" in skill
    assert "WB_API_TOKEN" in skill
    assert "python scripts/api_call.py" in skill
    assert "production-only" in readme.lower()
    assert "WB_API_TOKEN" in readme
