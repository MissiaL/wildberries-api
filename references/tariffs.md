# Tariffs

## Scope

- Product category commission, box tariffs, pallet tariffs, supply acceptance coefficients, and return tariffs.
- Primary schema: `assets/openapi/wb-tariffs.json`.
- Host: `common-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/v1/tariffs/commission"
python scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/v1/tariffs/box"
python scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/v1/tariffs/pallet"
python scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/tariffs/v1/acceptance/coefficients"
python scripts/api_call.py --method GET --url "https://common-api.wildberries.ru/api/v1/tariffs/return"
```

Tariff endpoints are read-only in the current snapshot; still preserve user filters and dates exactly.

