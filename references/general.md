# General

## Scope

- Connection checks, seller news, seller info, seller rating, Jam subscriptions, and user management.
- Primary schema: `assets/openapi/api-information.json`.
- Production hosts include `common-api.wildberries.ru` and `user-management-api.wildberries.ru`; the schema also carries the shared production host list.

## Auth

- Export `WB_API_TOKEN` before calling the API.
- Do not pass an `Authorization` header manually; `scripts/api_call.py` injects it.
- Token scopes must match the operation in WB seller settings. If WB returns a permission error, ask the user for a token with the matching scope.
- Token type affects limits. Personal, Service, and Basic production tokens have separate budgets. The helper selects the correct table row by decoding the token's JWT payload locally; never paste a token into an online decoder.

See [rate-limits.md](rate-limits.md) before repeated calls.

## Typical Calls

```bash
python3 scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/ping"
python3 scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/v1/seller-info"
python3 scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/common/v1/rating"
python3 scripts/api_call.py --method GET --url "https://user-management-api.wildberries.ru/api/v1/users"
```

For write operations such as inviting users or updating access, state the intended change before sending the request.
