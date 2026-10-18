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

For returns to the seller, prefer `GET https://seller-analytics-api.wildberries.ru/api/analytics/v1/item-returns`, with required `dateFrom` and `dateTo` and optional `status`, `limit`, and `offset`. The deprecated `GET /api/v1/analytics/goods-return` is scheduled to stop on 2026-10-26. Neither method currently publishes a rate limit; verify with WB before pagination or polling.

`GET /api/v1/analytics/region-sale` is deprecated and scheduled to stop on
**2026-11-03**. WB directs integrations to the Order Feed report,
`POST https://seller-analytics-api.wildberries.ru/api/analytics/v1/order-feed`;
this is a dataset for regional aggregation, not the same response schema.
Follow the [official migration notice](https://dev.wildberries.ru/en/release-notes?id=590)
and [regional aggregation instructions](https://dev.wildberries.ru/en/knowledge-base/articles/01a09d9e-4f79-7016-b641-0718252e6572/order-feed#sales-by-region).
