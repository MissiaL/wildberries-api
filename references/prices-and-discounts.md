# Prices And Discounts

## Scope

- Price and discount operations are routed through the product-management schema.
- Primary schema: `assets/openapi/work-with-products.json`.
- Host: `discounts-prices-api.wildberries.ru`.

## Typical Pattern

1. Inspect `assets/openapi/work-with-products.json` for the exact price or discount endpoint.
2. Confirm whether the request changes prices, discounts, or promo settings.
3. Send write requests only after stating the intended effect.

```bash
python scripts/api_call.py --method GET --url "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter"
python scripts/api_call.py --method POST --url "https://discounts-prices-api.wildberries.ru/api/v2/upload/task" --body '{"data":[]}'
```

Price changes are write operations with direct seller impact; never infer quantities, SKUs, or discount values.

