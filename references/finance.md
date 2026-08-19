# Finance

## Scope

- Seller balance, sales reports, acquiring expense reports, and realization reports.
- Primary schema: `assets/openapi/financial-reports-and-accounting.json`.
- Hosts: `finance-api.wildberries.ru` and `statistics-api.wildberries.ru`.

## Typical Calls

```bash
python3 scripts/api_call.py --method GET --url "https://finance-api.wildberries.ru/api/v1/account/balance"
python3 scripts/api_call.py --method POST --url "https://finance-api.wildberries.ru/api/finance/v1/sales-reports/list" --body '{}'
python3 scripts/api_call.py --method POST --url "https://finance-api.wildberries.ru/api/finance/v1/sales-reports/detailed" --body '{"dateFrom":"2026-04-01","dateTo":"2026-04-20"}'
python3 scripts/api_call.py --method POST --url "https://finance-api.wildberries.ru/api/finance/v1/acquiring/list" --body '{}'
```

Financial requests are high-stakes. Preserve exact report IDs, periods, currencies, and seller-supplied filters.

The sales-report list and report-by-ID methods require a Personal or Service token for the Finance category. Current documentation limits each detailed sales-report method to one request per minute with burst 1; verify the exact token-type row before calling.

Do not use deprecated `GET https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod`; WB scheduled it for shutdown on 2026-07-15. Use `POST /api/finance/v1/sales-reports/detailed` or `POST /api/finance/v1/sales-reports/detailed/{reportId}`.
