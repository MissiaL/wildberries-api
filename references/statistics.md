# Statistics

## Scope

- Supplier stocks, orders, sales, warehouse remains tasks, excise reports, and selected analytics reports.
- Primary schema: `assets/openapi/reports.json`.
- Related accounting schema: `assets/openapi/financial-reports-and-accounting.json`.
- Host: `statistics-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://statistics-api.wildberries.ru/api/v1/supplier/stocks" --params '{"dateFrom":"2026-04-01"}'
python scripts/api_call.py --method GET --url "https://statistics-api.wildberries.ru/api/v1/supplier/orders" --params '{"dateFrom":"2026-04-01"}'
python scripts/api_call.py --method GET --url "https://statistics-api.wildberries.ru/api/v1/supplier/sales" --params '{"dateFrom":"2026-04-01"}'
python scripts/api_call.py --method GET --url "https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod" --params '{"dateFrom":"2026-04-01","dateTo":"2026-04-20"}'
```

Statistics endpoints often require date bounds. Use absolute dates and avoid unbounded pulls unless the user explicitly asks.

