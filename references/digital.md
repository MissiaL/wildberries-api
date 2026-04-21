# Digital

The current fetched public OpenAPI snapshot does not expose a separate digital-goods schema page.

Use [overview.md](overview.md) and `assets/openapi/manifest.json` as the source of truth. If WB adds a digital page, refresh schemas with:

```bash
python scripts/fetch_openapi.py
```

Then route the new manifest slug from [overview.md](overview.md) and add a domain-specific guide.

