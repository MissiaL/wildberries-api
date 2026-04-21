# Supplies

## Scope

- FBW supply acceptance, warehouses, transit tariffs, supply list, supply details, supply products, and package details.
- Primary schema: `assets/openapi/orders-fbw.json`.
- Host: `supplies-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://supplies-api.wildberries.ru/api/v1/warehouses"
python scripts/api_call.py --method GET --url "https://supplies-api.wildberries.ru/api/v1/transit-tariffs"
python scripts/api_call.py --method POST --url "https://supplies-api.wildberries.ru/api/v1/acceptance/options" --body '{}'
python scripts/api_call.py --method GET --url "https://supplies-api.wildberries.ru/api/v1/supplies/123"
```

Create or modify supply workflows only after confirming warehouse, acceptance window, and product list.

