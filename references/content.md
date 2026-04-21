# Content

## Scope

- Product cards, categories, subject characteristics, directories, media, brands, tags, and marketplace product metadata.
- Primary schema: `assets/openapi/work-with-products.json`.
- Hosts: `content-api.wildberries.ru`, plus related product operations on `marketplace-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://content-api.wildberries.ru/content/v2/object/parent/all"
python scripts/api_call.py --method GET --url "https://content-api.wildberries.ru/content/v2/object/all" --params '{"locale":"en"}'
python scripts/api_call.py --method GET --url "https://content-api.wildberries.ru/content/v2/object/charcs/1234"
python scripts/api_call.py --method POST --url "https://content-api.wildberries.ru/content/v2/cards/upload" --body '{"cards":[]}'
```

## Notes

- For product-card creation or edits, validate required subject characteristics from `GET /content/v2/object/charcs/{subjectId}` first.
- Large uploads and destructive edits should be summarized to the user before execution.

