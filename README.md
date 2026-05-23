# Webhook Receiver

A simple, production-minded webhook receiver built with FastAPI.

Built to handle CRM events (`contact.created`, `contact.updated`) reliably — covering signature verification, idempotency, and structured logging.

---

## Features

- **Signature verification** — HMAC-SHA256, constant-time comparison, replay attack protection via timestamp check
- **Idempotency** — skips duplicate events using an in-memory store (Redis with TTL in production)
- **Structured logging** — every event logged with ID, type, and outcome
- **Async-ready** — returns 200 immediately; designed to hand off to a queue (e.g. SQS) for processing

---

## Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set your secret
cp example.env .env

# Start the server
uvicorn main:app --reload
```

---

## Sending a test event

```bash
python test_webhook.py
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook` | Receive CRM events |
| GET | `/health` | Health check |

---

## Required headers

| Header | Description |
|--------|-------------|
| `x-webhook-signature` | HMAC-SHA256 signature of `timestamp:body` |
| `x-webhook-timestamp` | Unix timestamp of the request |
| `x-event-id` | Unique event ID for idempotency |

---

## Notes

- Idempotency store is in-memory for simplicity. In production this would be Redis with a 24-hour TTL.
- In production the event would be pushed to a queue (SQS or similar) after the 200 response, and processed by a separate worker.
