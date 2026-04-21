# Promotion

## Scope

- Advertising campaigns, campaign information, bids, campaign creation, product cards for campaigns, launch, pause, rename, and delete actions.
- Primary schema: `assets/openapi/promotion.json`.
- Host: `advert-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://advert-api.wildberries.ru/adv/v1/promotion/count"
python scripts/api_call.py --method GET --url "https://advert-api.wildberries.ru/api/advert/v2/adverts"
python scripts/api_call.py --method POST --url "https://advert-api.wildberries.ru/api/advert/v1/bids/min" --body '{}'
python scripts/api_call.py --method GET --url "https://advert-api.wildberries.ru/adv/v1/supplier/subjects"
```

Campaign launch, pause, delete, rename, bid, and budget operations are write-impacting. State campaign IDs and intended changes before execution.

