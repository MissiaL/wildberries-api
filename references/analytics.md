# Analytics

## Scope

- Sales funnels, grouped product-card analytics, search reports, stock reports, warehouse inventory, and seller analytics reports.
- Schemas: `assets/openapi/analytics.json` and analytics sections in `assets/openapi/reports.json`.
- Host: `seller-analytics-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method POST --url "https://seller-analytics-api.wildberries.ru/api/analytics/v3/sales-funnel/products" --body '{"period":{"begin":"2026-04-01","end":"2026-04-20"},"page":1}'
python scripts/api_call.py --method POST --url "https://seller-analytics-api.wildberries.ru/api/v2/search-report/report" --body '{}'
python scripts/api_call.py --method POST --url "https://seller-analytics-api.wildberries.ru/api/analytics/v1/stocks-report/wb-warehouses" --body '{}'
```

Use date ranges exactly as WB expects for the operation. For long-running report endpoints, create the task first, then poll/download according to the schema path.

