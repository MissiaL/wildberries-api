# Returns

## Scope

- Buyer and seller communication around returns in the customer-communication schema.
- Primary schema: `assets/openapi/user-communication.json`.
- Host: `returns-api.wildberries.ru`.

## Typical Pattern

1. Inspect `assets/openapi/user-communication.json` for paths served by `returns-api.wildberries.ru`.
2. Fetch return records before attempting status changes or responses.
3. Confirm return IDs and intended seller action before write requests.

```bash
python scripts/api_call.py --method GET --url "https://returns-api.wildberries.ru/api/v1/claims"
python scripts/api_call.py --method PATCH --url "https://returns-api.wildberries.ru/api/v1/claim" --body '{}'
```

If an endpoint is absent from the current snapshot, refresh schemas with `python scripts/fetch_openapi.py` and re-check `manifest.json`.
