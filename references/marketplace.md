# Marketplace Orders

## Scope

- FBS, DBS, DBW, and in-store pickup orders.
- Schemas: `assets/openapi/orders-fbs.json`, `assets/openapi/orders-dbs.json`, `assets/openapi/orders-dbw.json`, `assets/openapi/in-store-pickup.json`.
- Host: `marketplace-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://marketplace-api.wildberries.ru/api/v3/orders/new"
python scripts/api_call.py --method GET --url "https://marketplace-api.wildberries.ru/api/v3/dbs/orders/new"
python scripts/api_call.py --method GET --url "https://marketplace-api.wildberries.ru/api/v3/dbw/orders/new"
python scripts/api_call.py --method GET --url "https://marketplace-api.wildberries.ru/api/v3/click-collect/orders/new"
python scripts/api_call.py --method POST --url "https://marketplace-api.wildberries.ru/api/v3/orders/status" --body '{"orders":[]}'
```

## Write Safety

- Status transitions, cancellations, sticker generation, and delivery-date changes are write-impacting operations.
- Before sending a write request, state the order IDs and target status/action.

