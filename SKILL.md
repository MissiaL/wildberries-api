---
name: wildberries-api
description: Use when the user needs to read or change Wildberries seller data through the official production API, including product cards, prices, orders, supplies, analytics, promotions, reviews, reports, finance, returns, documents, tariffs, and seller operations.
metadata: {"author":"MissiaL","version":"0.1.0","keywords":["wildberries","seller-api","marketplace","product-cards","prices","orders","analytics","promotions","reports","finance"]}
---

# Wildberries API

Use this skill to work with the official Wildberries seller API in production.

## Setup

- Export `WB_API_TOKEN` before calling the API.
- This skill is production-only; sandbox and non-Wildberries hosts are blocked.
- Use only `python scripts/api_call.py` for API calls so host allowlisting, auth injection, and error sanitization are applied.

## Call Pattern

```bash
python scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/ping"
python scripts/api_call.py --method POST --url "https://content-api.wildberries.ru/content/v2/cards/upload" --body '{"cards":[]}'
```

`--params`, `--body`, and `--headers` must be valid JSON objects. Do not include `Authorization`; the helper reads `WB_API_TOKEN` and adds it.

## Routing

- Start with [references/overview.md](references/overview.md) to choose the schema and domain guide.
- Use [references/general.md](references/general.md) for auth, token scopes, seller info, and common API behavior.
- Inspect `assets/openapi/manifest.json` for fetched schema coverage and provenance.
- Inspect the matching `assets/openapi/*.json` file before complex requests.

## Rules

- Read requests may run directly when the user has asked for the data.
- For write-impacting requests, briefly state the intended entity IDs and action before sending the request.
- Never invent seller IDs, order IDs, nmIDs, barcodes, prices, discounts, dates, or report IDs.
- Preserve user-provided filters exactly; use absolute dates for dated reports and analytics.
- If WB returns an auth or scope error, explain the missing permission and ask for a token with the matching WB seller scope.
- Do not use sandbox endpoints, mock tokens, browser sessions, cookies, or manually supplied authorization headers.

## Coverage

Local OpenAPI snapshots cover product management, prices and discounts, FBS/DBS/DBW/in-store orders, FBW supplies, promotion, customer communication, tariffs, analytics, reports, finance, documents, returns, buyer chat, and general seller operations.

Supported coverage is the set of schemas listed in `assets/openapi/manifest.json`, with production-only hosts from `assets/openapi/host-allowlist.json`.
