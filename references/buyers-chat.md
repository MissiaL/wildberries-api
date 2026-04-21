# Buyers Chat

## Scope

- Buyer chat operations covered by the customer-communication schema.
- Primary schema: `assets/openapi/user-communication.json`.
- Host: `buyer-chat-api.wildberries.ru`.

## Typical Pattern

1. Inspect `assets/openapi/user-communication.json` for buyer-chat paths.
2. Fetch conversation state before sending messages.
3. Confirm message text, chat ID, and attachments before write requests.

```bash
python scripts/api_call.py --method GET --url "https://buyer-chat-api.wildberries.ru/api/v1/seller/chats"
```

Chat messages are externally visible. Do not draft or send final text without user confirmation when the user did not provide exact wording.

