# Rate Limits

Read this before repeated, parallel, paginated, or polling calls.

## Sources and Freshness

Rate limits are live operational data and can change independently of endpoint schemas. Check the official table for the exact method immediately before a series of calls:

- [WB API documentation](https://dev.wildberries.ru/docs/openapi/api-information)
- [Rate-limit knowledge-base article, updated 2026-04-03](https://dev.wildberries.ru/knowledge-base/articles/019d49a1-28ca-7735-bf2f-98210695abc7/limity-zaprosov-wb-api)
- [Token-type limit change effective 2026-03-30](https://dev.wildberries.ru/news/281/obnovlenie-limitov-zaprosov-wb-api)

Every saved OpenAPI operation carries the live table captured on 2026-07-29 in `x-wb-rate-limits`. `assets/openapi/rate-limit-manifest.json` records coverage and verification time. Never infer a limit from a similar endpoint; if the saved `verifiedAt` may be stale, re-check the exact live operation.

## Model

WB uses a token-bucket algorithm. Read all four values in the method's table:

- `Period`: accounting window.
- `Limit`: maximum request cost in that period.
- `Interval`: normal pause between calls. Use this for steady traffic.
- `Burst`: temporary requests allowed without interval pauses. It is headroom, not the normal concurrency target.

Limits can differ by method or method group and by token type. Since 2026-03-30, Personal, Service, Basic, and Test tokens have independent budgets:

- Personal and Service tokens use the standard production limits shown for those types.
- Basic tokens can have materially lower limits; use the Basic-token tables in the official announcement.
- Test tokens belong to the sandbox and are outside this production-only skill.
- A limit normally covers all tokens of one type for the seller account. For Service tokens, it covers all tokens for the same Catalog service.

Do not multiply throughput by creating more tokens or workers. All processes that share the same WB budget must use one coordinated limiter.

The Marketplace example in current WB documentation illustrates why token type matters: Personal and Service tokens are listed at 300 requests per minute with burst 20, while Basic tokens are listed at 150 requests per minute with burst 10. This is an example for that category, not a default for other methods.

## Before Calling

1. Identify the exact host, path, method, seller account, and token type. `api_call.py` decodes only the local JWT payload to select the token-type row; it never sends the token anywhere except the requested allowlisted WB host.
2. Inspect `x-wb-rate-limits` on the exact local operation or run `api_call.py ... --show-rate-limit`. Re-open the live method page when the saved verification time may be stale.
3. Prefer batch endpoints, maximum safe page sizes, incremental date cursors, and cached dictionaries.
4. For pagination or polling, wait at least `Interval` between requests. Do not launch independent page workers unless they share a limiter.
5. Watch stderr from `scripts/api_call.py`. On non-429 responses it reports `X-Ratelimit-Remaining` when WB sends it. Slow down before the remaining burst reaches zero.

Many current operation descriptions state that one `4XX` response costs 10 ordinary requests. The general knowledge-base explanation also notes method groups where a `409` costs 5 or 10. Always follow the exact note saved on the operation. Validate payloads and state transitions first; never create a `4XX` retry loop.

If the exact token type has no row in the method table, do not substitute another token type's limit. Treat the method as unavailable or unverified for that token until the live documentation confirms otherwise.

## Handling 429

WB omits `X-Ratelimit-Remaining` on `429` and returns recovery information instead:

- `X-Ratelimit-Retry`: seconds before the next allowed attempt.
- `X-Ratelimit-Reset`: seconds until the burst is fully restored.
- `X-Ratelimit-Limit`: restored burst size.
- Response body `detail`: method-specific guidance.

The helper follows this policy:

1. Retry only after `X-Ratelimit-Retry`; never retry earlier.
2. If the header is absent or invalid, use exponential delays of 1, 2, then 4 seconds.
3. Stop after 3 retries by default. Never create an infinite retry loop.
4. If one requested delay exceeds `--max-wait` (60 seconds by default), return the `429` with its rate-limit metadata instead of blocking unexpectedly.

Example:

```bash
python scripts/api_call.py \
  --method GET \
  --url "https://common-api.wildberries.ru/ping" \
  --max-retries 3 \
  --max-wait 60
```

For a scheduled integration, persist the next-allowed time and release the worker instead of holding it asleep for a long Basic-token cooldown.

## Other Errors

- `401` and `403`: fix token validity, category, type, or access; do not back off as if rate-limited.
- `4xx`: fix authorization, payload, or state instead of retrying blindly. Account for the exact operation's documented request-cost multiplier.
- `5xx` or network timeout on a read: retry cautiously with bounded exponential backoff and jitter.
- `5xx` or network timeout on a write: verify whether the change was applied before retrying. The helper intentionally does not auto-retry these responses.
