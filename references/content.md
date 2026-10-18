# Content

## Scope

- Product cards, categories, subject characteristics, directories, media, brands, tags, and marketplace product metadata.
- Primary schema: `assets/openapi/work-with-products.json`.
- Hosts: `content-api.wildberries.ru`, plus related product operations on `marketplace-api.wildberries.ru`.

## Typical Calls

```bash
python3 scripts/api_call.py --method GET --url "https://content-api.wildberries.ru/content/v2/object/parent/all"
python3 scripts/api_call.py --method GET --url "https://content-api.wildberries.ru/content/v2/object/all" --params '{"locale":"en"}'
python3 scripts/api_call.py --method GET --url "https://content-api.wildberries.ru/content/v2/object/charcs/1234"
python3 scripts/api_call.py --method POST --url "https://content-api.wildberries.ru/content/v2/get/cards/list" --body '{"settings":{"cursor":{"limit":100},"filter":{"withPhoto":-1}}}'
```

## Notes

- For product-card creation or edits, validate required subject characteristics from `GET /content/v2/object/charcs/{subjectId}` first.
- `/content/v2/cards/upload` and `/content/v2/cards/update` take JSON arrays, not a `{"cards": [...]}` wrapper. Use the exact operation schema and real subject, characteristic, and item IDs.
- Large uploads and destructive edits should be summarized to the user before execution.
- Current classification directories include `GET /api/content/v2/directory/okpd`, `/api/content/v2/directory/okpd/all`, and `/api/content/v2/directory/tnved/all`; inspect their query parameters before paginating.
