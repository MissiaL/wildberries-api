# Wildberries API

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Production-only agent skill for the official Wildberries seller API. It bundles local OpenAPI snapshots, category references, and a safe Python helper that injects `WB_API_TOKEN`, blocks non-production hosts, and handles HTTP 429 according to WB rate-limit headers.

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
python3 scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/ping"
```

This skill is production-only. Sandbox hosts and test-token workflows are intentionally excluded.

For repeated calls, read [`references/rate-limits.md`](references/rate-limits.md). The 2026-10-03 snapshot contains 307 operations: 305 have documented limits and two return-report operations are explicitly marked `undocumented`. Current counts and sources live in `assets/openapi/rate-limit-manifest.json`. The helper can show the exact host/method/token-type profile with `--show-rate-limit`, retries `429` up to three times, honors `X-Ratelimit-Retry`, and caps a single wait at 60 seconds.

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

## Supported Coverage

- All fetched production schemas listed in `assets/openapi/manifest.json`
- Category routing in `references/overview.md`
- Current rate-limit workflow in `references/rate-limits.md`
- Production-only hosts from `assets/openapi/host-allowlist.json`

## Development

```bash
python3 -m pytest -v
python3 scripts/fetch_openapi.py
python3 scripts/sync_openapi.py /tmp/wb-live-specs.json --captured-at <ISO-8601-time>
```

`fetch_openapi.py` downloads the 13 official Swagger YAML files from the source URLs in the manifest and runs the existing sync. Documentation HTML can return anti-bot HTTP 498, while these public YAML downloads return HTTP 200. To rediscover changed source URLs, open the official Swagger pages in a browser and follow their `swagger.yaml` links. The sync also accepts a JSON object of specifications keyed by documentation slug; it records absent limits explicitly instead of retaining stale tables.

## License

MIT
