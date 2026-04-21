# Feedbacks And Questions

## Scope

- Product questions, feedbacks, unanswered counts, unseen activity, feedback replies, and question handling.
- Primary schema: `assets/openapi/user-communication.json`.
- Host: `feedbacks-api.wildberries.ru`.

## Typical Calls

```bash
python scripts/api_call.py --method GET --url "https://feedbacks-api.wildberries.ru/api/v1/new-feedbacks-questions"
python scripts/api_call.py --method GET --url "https://feedbacks-api.wildberries.ru/api/v1/questions/count-unanswered"
python scripts/api_call.py --method GET --url "https://feedbacks-api.wildberries.ru/api/v1/questions"
python scripts/api_call.py --method GET --url "https://feedbacks-api.wildberries.ru/api/v1/feedbacks"
python scripts/api_call.py --method POST --url "https://feedbacks-api.wildberries.ru/api/v1/feedbacks/answer" --body '{}'
```

Replies and question updates are seller-visible writes. Confirm the text, feedback/question ID, and target action before sending.

