# Digital

The current browser-captured public OpenAPI inventory does not expose a separate digital-goods schema page.

Use [overview.md](overview.md) and `assets/openapi/manifest.json` as the source of truth. If WB adds a digital page, refresh schemas with:

Capture the new rendered `__redoc_state.spec.data` object together with the
other official pages, then run `python3 scripts/sync_openapi.py <export.json>`.

Then route the new manifest slug from [overview.md](overview.md) and add a domain-specific guide.
