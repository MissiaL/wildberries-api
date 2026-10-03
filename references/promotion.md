# Promotion

## Scope

- Advertising campaigns, campaign information, bids, budgets, daily limits, campaign creation, product cards for campaigns, launch, pause, rename, and delete actions.
- Primary schema: `assets/openapi/promotion.json`.
- Hosts: `advert-api.wildberries.ru`, `advert-media-api.wildberries.ru` for media campaigns, and `dp-calendar-api.wildberries.ru` for the promotion calendar. Match the path-level `servers` entry before a call.

## Typical Calls

```bash
python3 scripts/api_call.py --method GET --url "https://advert-api.wildberries.ru/adv/v1/promotion/count"
python3 scripts/api_call.py --method GET --url "https://advert-api.wildberries.ru/api/advert/v2/adverts"
python3 scripts/api_call.py --method POST --url "https://advert-api.wildberries.ru/api/advert/v1/bids/min" --body '{}'
python3 scripts/api_call.py --method GET --url "https://advert-api.wildberries.ru/adv/v1/supplier/subjects"
```

Campaign launch, pause, delete, rename, bid, and budget operations are write-impacting. State campaign IDs and intended changes before execution.

For budget balances, prefer `POST /api/advert/v2/budget`; this is a read method despite using POST. The deprecated `GET /adv/v1/budget` is scheduled to stop on 2026-11-16. Daily limits use `GET` and `PUT /api/advert/v0/daily-limits`; PUT changes campaign spending limits.
