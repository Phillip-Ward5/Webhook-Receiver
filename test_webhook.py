"""
Simulates a CRM sending a signed webhook event to our receiver.
Run with: python test_webhook.py
"""

import hmac
import hashlib
import time
import json
import uuid
import urllib.request

SECRET = "dev-secret"
URL = "http://localhost:8000/webhook"

# Build the payload
payload = {
    "event_type": "contact.created",
    "contact": {
        "id": "abc123",
        "name": "Jane Doe",
        "phone": "+14155550100"
    }
}
body = json.dumps(payload).encode()
timestamp = str(int(time.time()))
event_id = str(uuid.uuid4())

# Sign the request
message = f"{timestamp}:{body.decode()}".encode()
signature = hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()

# Send the request
req = urllib.request.Request(
    URL,
    data=body,
    headers={
        "Content-Type": "application/json",
        "x-webhook-signature": signature,
        "x-webhook-timestamp": timestamp,
        "x-event-id": event_id,
    },
    method="POST"
)

with urllib.request.urlopen(req) as response:
    print(f"Status: {response.status}")
    print(f"Response: {response.read().decode()}")
