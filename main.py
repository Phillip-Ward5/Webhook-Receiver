import hmac
import hashlib
import time
import logging
import os

from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

# --- Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Webhook Receiver")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret")
MAX_TIMESTAMP_AGE = 300  # 5 minutes in seconds

# In-memory idempotency store
# In production this would be Redis with a TTL
seen_event_ids: set = set()


# --- Signature Verification ---
def verify_signature(payload: bytes, signature: str, timestamp: str) -> bool:
    """
    Recompute the HMAC-SHA256 signature and compare it to what the CRM sent.
    Also checks the timestamp to block replay attacks.
    """
    # Reject requests older than 5 minutes
    try:
        request_time = int(timestamp)
    except ValueError:
        return False

    if abs(time.time() - request_time) > MAX_TIMESTAMP_AGE:
        logger.warning("Rejected request: timestamp too old")
        return False

    # Recompute signature: HMAC over timestamp + payload
    message = f"{timestamp}:{payload.decode('utf-8')}".encode()
    expected = hmac.new(WEBHOOK_SECRET.encode(), message, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, signature)


# --- Idempotency Check ---
def is_duplicate(event_id: str) -> bool:
    if event_id in seen_event_ids:
        return True
    seen_event_ids.add(event_id)
    return False


# --- Webhook Endpoint ---
@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_webhook_signature: str = Header(...),
    x_webhook_timestamp: str = Header(...),
    x_event_id: str = Header(...),
):
    payload = await request.body()

    # Step 1: Verify signature
    if not verify_signature(payload, x_webhook_signature, x_webhook_timestamp):
        logger.warning("Rejected request: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Step 2: Idempotency check
    if is_duplicate(x_event_id):
        logger.info(f"Duplicate event received and skipped: {x_event_id}")
        return {"status": "already processed"}

    # Step 3: Parse and log the event
    try:
        body = await request.json()
    except Exception:
        body = payload.decode("utf-8")

    event_type = body.get("event_type", "unknown") if isinstance(body, dict) else "unknown"

    logger.info(f"Event received | id={x_event_id} type={event_type}")

    # Step 4: Acknowledge immediately
    # In production, event would be pushed to a queue here (e.g. SQS, Redis)
    # and processed asynchronously by a worker
    return {"status": "received", "event_id": x_event_id}


# --- Health Check ---
@app.get("/health")
def health():
    return {"status": "ok"}
