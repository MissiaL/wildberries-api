---
name: wildberries-api
description: Use when the user needs to read or change Wildberries (WB, вайлдберриз, вб) seller data through the official production API, including product cards, prices, orders, supplies, analytics, promotions, reviews, reports, finance, returns, documents, tariffs, and seller operations.
metadata: {"author":"MissiaL","version":"0.4.0","keywords":["wildberries","wb","вайлдберриз","вб","seller-api","marketplace","product-cards","prices","orders","analytics","promotions","reports","finance","rate-limits"]}
---

# Wildberries API

Use this skill to work with the official Wildberries seller API in production.

## Setup

- Export `WB_API_TOKEN` before calling the API.
- This skill is production-only; sandbox and non-Wildberries hosts are blocked.
- Use only `python3 scripts/api_call.py` for API calls so host allowlisting, auth injection, and error sanitization are applied.
- Before any repeated or paginated calls, read [references/rate-limits.md](references/rate-limits.md) and identify the token type and the exact method's current limit.

## Call Pattern

```bash
python3 scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/ping"
python3 scripts/api_call.py --method POST --url "https://content-api.wildberries.ru/content/v2/cards/upload" --body '{"cards":[]}'
```

`--params`, `--body`, and `--headers` must be valid JSON objects. Do not include `Authorization`; the helper reads `WB_API_TOKEN` and adds it.

The helper retries only HTTP `429`, up to 3 times by default. It waits for `X-Ratelimit-Retry`, never sleeps more than 60 seconds for one retry, and prints returned rate-limit state to stderr. Use `--max-retries 0` to inspect a `429` without retrying, or change `--max-wait` when the user explicitly accepts a longer wait.

Before a series of calls, inspect the exact verified profile without sending a request:

```bash
python3 scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/v1/seller-info" --show-rate-limit
```

## Routing

- Start with [references/overview.md](references/overview.md) to choose the schema and domain guide.
- Use [references/general.md](references/general.md) for auth, token scopes, seller info, and common API behavior.
- Use [references/rate-limits.md](references/rate-limits.md) for token buckets, token-type limits, scheduling, headers, and retry rules.
- Inspect `assets/openapi/manifest.json` for browser-captured schema coverage and provenance.
- Inspect the matching `assets/openapi/*.json` file before complex requests.

## Rules

- Read requests may run directly when the user has asked for the data.
- For write-impacting requests, briefly state the intended entity IDs and action before sending the request.
- Never invent seller IDs, order IDs, nmIDs, barcodes, prices, discounts, dates, or report IDs.
- Preserve user-provided filters exactly; use absolute dates for dated reports and analytics.
- If WB returns an auth or scope error, explain the missing permission and ask for a token with the matching WB seller scope.
- Do not use sandbox endpoints, mock tokens, browser sessions, cookies, or manually supplied authorization headers.
- Never assume one global WB limit or reuse a limit from another method. Each local operation now carries its verified table in `x-wb-rate-limits`; if its `verifiedAt` may be stale, re-check the exact live method page before a batch.
- Pace repeated requests by the documented `Interval`; treat `Burst` as short headroom, not as the normal concurrency target. Coordinate parallel workers against one shared budget.
- On `429`, obey `X-Ratelimit-Retry`; do not retry early or indefinitely. Do not retry `4XX` blindly: many live method descriptions charge one `4XX` as 10 requests, and the exact operation note in `x-wb-rate-limits` wins.
- Do not automatically retry `401`, `403`, or write-request timeouts/`5xx`. Their causes are not rate limits, and a write may already have been applied.

## Coverage

Local OpenAPI snapshots cover product management, prices and discounts, FBS/DBS/DBW/in-store orders, FBW supplies, promotion, customer communication, tariffs, analytics, reports, finance, documents, returns, buyer chat, and general seller operations.

Supported coverage is the set of schemas listed in `assets/openapi/manifest.json`, with production-only hosts from `assets/openapi/host-allowlist.json`.
