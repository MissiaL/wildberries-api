# Supplies

## Scope

- FBW supply acceptance, warehouses, transit tariffs, supply list, supply details, supply products, packages, supply drafts, draft items, and acceptance discrepancies.
- Primary schema: `assets/openapi/orders-fbw.json`.
- Host: `supplies-api.wildberries.ru`.

## Typical Calls

```bash
python3 scripts/api_call.py --method GET --url "https://supplies-api.wildberries.ru/api/v1/warehouses"
python3 scripts/api_call.py --method GET --url "https://supplies-api.wildberries.ru/api/v1/transit-tariffs"
python3 scripts/api_call.py --method POST --url "https://supplies-api.wildberries.ru/api/v1/acceptance/options" --body '{}'
python3 scripts/api_call.py --method GET --url "https://supplies-api.wildberries.ru/api/v1/supplies/123"
```

Create or modify supply workflows only after confirming warehouse, acceptance window, and product list.

The `/api/supplies/v1/drafts` methods create, list, fill, and delete drafts and draft items; these and `GET /api/supplies/v1/discrepancies/{supplyId}` require a Personal or Service token. Validate draft IDs and item quantities before changing a draft.
