# Documents

## Scope

- Document categories, document lists, document details, and document download workflows.
- Primary schema: `assets/openapi/financial-reports-and-accounting.json`.
- Host: `documents-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://documents-api.wildberries.ru/api/v1/documents/categories"
python scripts/api_call.py --method GET --url "https://documents-api.wildberries.ru/api/v1/documents/list"
```

When downloading or retrieving document details, keep the WB document ID exactly as provided by the API or user.

