# Wildberries API Overview

Use this file first to route a seller API request to the right local schema and category guide.

All calls are production-only. Use `scripts/api_call.py`; it reads `WB_API_TOKEN`, injects `Authorization`, and blocks hosts not listed in `assets/openapi/host-allowlist.json`.

## Schema Routing

| Slug | Title | Hosts | Schema | Guide |
| --- | --- | --- | --- | --- |
| `api-information` | General | `common-api.wildberries.ru`, `user-management-api.wildberries.ru` and shared production hosts | `api-information.json` | [general.md](general.md) |
| `work-with-products` | Product Management | `content-api.wildberries.ru`, `discounts-prices-api.wildberries.ru`, `marketplace-api.wildberries.ru` | `work-with-products.json` | [content.md](content.md), [prices-and-discounts.md](prices-and-discounts.md) |
| `orders-fbs` | FBS Orders | `marketplace-api.wildberries.ru` | `orders-fbs.json` | [marketplace.md](marketplace.md) |
| `orders-dbw` | DBW Orders | `marketplace-api.wildberries.ru` | `orders-dbw.json` | [marketplace.md](marketplace.md) |
| `orders-dbs` | DBS Orders | `marketplace-api.wildberries.ru` | `orders-dbs.json` | [marketplace.md](marketplace.md) |
| `in-store-pickup` | In-Store Pickup Orders | `marketplace-api.wildberries.ru` | `in-store-pickup.json` | [marketplace.md](marketplace.md) |
| `orders-fbw` | FBW Supplies | `supplies-api.wildberries.ru` | `orders-fbw.json` | [supplies.md](supplies.md) |
| `promotion` | Marketing and Promotions | `advert-api.wildberries.ru` | `promotion.json` | [promotion.md](promotion.md) |
| `user-communication` | Customer Communication | `feedbacks-api.wildberries.ru`, `buyer-chat-api.wildberries.ru`, `returns-api.wildberries.ru` | `user-communication.json` | [feedbacks-and-questions.md](feedbacks-and-questions.md), [buyers-chat.md](buyers-chat.md), [returns.md](returns.md) |
| `wb-tariffs` | Tariffs | `common-api.wildberries.ru` | `wb-tariffs.json` | [tariffs.md](tariffs.md) |
| `analytics` | Analytics and Data | `seller-analytics-api.wildberries.ru` | `analytics.json` | [analytics.md](analytics.md) |
| `reports` | Reports | `statistics-api.wildberries.ru`, `seller-analytics-api.wildberries.ru` | `reports.json` | [statistics.md](statistics.md), [analytics.md](analytics.md) |
| `financial-reports-and-accounting` | Documents and Accounting | `finance-api.wildberries.ru`, `statistics-api.wildberries.ru`, `documents-api.wildberries.ru` | `financial-reports-and-accounting.json` | [finance.md](finance.md), [documents.md](documents.md) |

## Working Pattern

1. Pick the relevant row above.
2. Open the guide named in the `Guide` column for domain caveats.
3. Inspect the schema in `assets/openapi/<schema>` for exact paths, methods, and operation summaries.
4. Send the request through `python scripts/api_call.py --method ... --url ...`.

