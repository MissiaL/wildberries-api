# Analytics

## Scope

- Sales funnels, grouped product-card analytics, search reports, stock reports, warehouse inventory, and seller analytics reports.
- Schemas: `assets/openapi/analytics.json` and analytics sections in `assets/openapi/reports.json`.
- Host: `seller-analytics-api.wildberries.ru`.

## Typical Calls

```bash
python3 scripts/api_call.py --method POST --url "https://seller-analytics-api.wildberries.ru/api/analytics/v3/sales-funnel/products" --body '{"selectedPeriod":{"start":"2026-10-12","end":"2026-10-17"},"limit":100,"offset":0}'
python3 scripts/api_call.py --method POST --url "https://seller-analytics-api.wildberries.ru/api/analytics/v1/order-feed" --body '{"selectedPeriod":{"start":"2026-10-17T00:00:00+03:00","end":"2026-10-18T00:00:00+03:00"},"pagination":{"limit":100,"offset":0}}'
python3 scripts/api_call.py --method POST --url "https://seller-analytics-api.wildberries.ru/api/analytics/v1/stocks-report/wb-warehouses" --body '{}'
```

Use date ranges exactly as WB expects for the operation. For long-running report endpoints, create the task first, then poll/download according to the schema path.

Dates above are examples captured on 2026-10-18; replace them with the user's
period within the method's current history window. Order Feed supports the
last 31 days. For subsequent Order Feed pages, reuse `pagination.snapshotTime`
from the first response; changing filters or the period starts a new selection.

Since **2026-10-12**, search-query reports and their CSV exports update once
every two hours. Sales-funnel reports also use a two-hour update cycle. For
current orders and sales, consider Order Feed rather than polling cached
reports faster. See the [search-report notice](https://dev.wildberries.ru/en/release-notes?id=594).

The `SEARCH_QUERIES_PREMIUM_REPORT_TEXT` CSV export no longer includes
`OpenCardPercentile`, `AddToCartPercentile`, `OpenToCartPercentile`,
`OrdersPercentile`, or `CartToOrderPercentile` from **2026-10-12**. Update CSV
parsers accordingly; see the [official notice](https://dev.wildberries.ru/en/release-notes?id=589).

`POST /api/analytics/v1/stocks-report/seller-warehouses` reports seller-warehouse inventory with a Personal or Service token. Its data updates every 30 minutes and its documented steady request interval is 20 seconds. Check the schema for filters and pagination.
