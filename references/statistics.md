# Statistics

## Scope

- Supplier orders, sales, warehouse remains tasks, excise reports, and selected analytics reports.
- Primary schema: `assets/openapi/reports.json`.
- Related accounting schema: `assets/openapi/financial-reports-and-accounting.json`.
- Host: `statistics-api.wildberries.ru`.

## Typical Calls

```bash
python3 scripts/api_call.py --method GET --url "https://statistics-api.wildberries.ru/api/v1/supplier/orders" --params '{"dateFrom":"2026-04-01"}'
python3 scripts/api_call.py --method GET --url "https://statistics-api.wildberries.ru/api/v1/supplier/sales" --params '{"dateFrom":"2026-04-01"}'
```

Statistics endpoints often require date bounds. Use absolute dates and avoid unbounded pulls unless the user explicitly asks.

Do not call deprecated `GET /api/v1/supplier/stocks`; WB scheduled it for shutdown on 2026-06-23. Use `POST https://seller-analytics-api.wildberries.ru/api/analytics/v1/stocks-report/wb-warehouses` with an Analytics Personal or Service token. Its documented steady limit is one request per 20 seconds.

Do not call deprecated `GET /api/v5/supplier/reportDetailByPeriod`; WB scheduled it for shutdown on 2026-07-15. Use the Finance API methods described in [finance.md](finance.md).
