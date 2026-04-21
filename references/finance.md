# Finance

## Scope

- Seller balance, sales reports, acquiring expense reports, and realization reports.
- Primary schema: `assets/openapi/financial-reports-and-accounting.json`.
- Hosts: `finance-api.wildberries.ru` and `statistics-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://finance-api.wildberries.ru/api/v1/account/balance"
python scripts/api_call.py --method POST --url "https://finance-api.wildberries.ru/api/finance/v1/sales-reports/list" --body '{}'
python scripts/api_call.py --method POST --url "https://finance-api.wildberries.ru/api/finance/v1/acquiring/list" --body '{}'
python scripts/api_call.py --method GET --url "https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod" --params '{"dateFrom":"2026-04-01","dateTo":"2026-04-20"}'
```

Financial requests are high-stakes. Preserve exact report IDs, periods, currencies, and seller-supplied filters.

