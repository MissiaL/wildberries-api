# Wildberries API

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Production-only agent skill for the official Wildberries seller API. It bundles local OpenAPI snapshots, category references, and a safe Python helper that injects `WB_API_TOKEN` and blocks non-production hosts.

## Compatible Agents

Works with AI agents that load `SKILL.md`-style skills and bundled resources. The repository follows the agent-documentation idea from [AGENTS.md](https://agents.md/): keep operational instructions predictable, concise, and close to the code.

## Requirements

- Python 3.8+
- Internet access
- `WB_API_TOKEN` with the required Wildberries seller scopes

## Installation

```bash
git clone https://github.com/MissiaL/wildberries-api.git wildberries-api
```

The directory name should match the skill name: `wildberries-api`.

## Quick Check

```bash
export WB_API_TOKEN="wb-production-token"
python scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/ping"
```

This skill is production-only. Sandbox hosts and test-token workflows are intentionally excluded.

## How It Works

```
User asks for WB seller data or an operation
  |
  v
Agent reads SKILL.md -> routes through references/overview.md
  |
  v
Agent checks assets/openapi/*.json for path and method
  |
  v
scripts/api_call.py validates host, injects WB_API_TOKEN, calls WB API
```

## API Coverage

- General seller operations and user management
- Product cards, directories, content, prices, and discounts
- FBS, DBS, DBW, in-store pickup, and FBW supply workflows
- Promotion and advertising campaigns
- Feedbacks, questions, buyer chat, claims, and returns
- Analytics, statistics, reports, finance, documents, and tariffs

The authoritative coverage list is `assets/openapi/manifest.json`; allowed production hosts live in `assets/openapi/host-allowlist.json`.

## Development

```bash
python -m pytest -v
python scripts/fetch_openapi.py
```

Use `scripts/fetch_openapi.py` to refresh the saved schemas from the official Wildberries documentation at `https://dev.wildberries.ru/docs/openapi/api-information`.

## License

MIT

