import os
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Notification Service - Hubtel SMS")

@app.get("/health")
def health():
    return {"status": "ok", "service": "notification"}

HUBTEL_CLIENT_ID = os.environ.get("HUBTEL_CLIENT_ID")
HUBTEL_CLIENT_SECRET = os.environ.get("HUBTEL_CLIENT_SECRET")
HUBTEL_SMS_SENDER = os.environ.get("HUBTEL_SMS_SENDER", "DELIVERY")
HUBTEL_SMS_API = os.environ.get("HUBTEL_SMS_API", "https://api.hubtel.com/v1/messages/sms")

# In-memory message store: (company_id, rider_id) -> list of messages
dialogs: Dict[str, List[dict]] = {}


class SmsRequest(BaseModel):
    phone: str
    message: str
    reference: Optional[str] = None


class Message(BaseModel):
    sender: str  # 'admin' or 'rider'
    recipient: str  # 'rider' or 'admin'
    company_id: str
    rider_id: str
    content: str
    timestamp: int
    is_alert: bool = False


class EventNotifyRequest(BaseModel):
    phone: str
    event: str
    order_id: Optional[str] = None


@app.post("/sms/send")
async def send_sms(req: SmsRequest):
    if not HUBTEL_CLIENT_ID or not HUBTEL_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Hubtel credentials not configured")

    payload = {
        "From": HUBTEL_SMS_SENDER,
        "To": req.phone,
        "Content": req.message,
    }

    async with httpx.AsyncClient(auth=(HUBTEL_CLIENT_ID, HUBTEL_CLIENT_SECRET), timeout=10.0) as client:
        try:
            r = await client.post(HUBTEL_SMS_API, json=payload)
            r.raise_for_status()
            return {"ok": True, "hubtel_response": r.json()}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Hubtel API error: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Hubtel request failed: {str(e)}")


@app.post("/notify/event")
async def notify_event(req: EventNotifyRequest):
    # Simple event->message mapping; expand templates as needed.
    msg_map = {
        "order_placed": lambda o: f"Your order {o} has been placed. We'll notify you when a rider is assigned.",
        "rider_assigned": lambda o: f"A rider has been assigned to your order {o}. You will receive tracking link shortly.",
        "pickup_confirmed": lambda o: f"Pickup confirmed for order {o}.",
        "delivery_completed": lambda o: f"Delivery completed for order {o}. Thank you!",
        "tracking_link": lambda o: f"Track your order {o}: <link>",
    }

    template = msg_map.get(req.event)
    if not template:
        raise HTTPException(status_code=400, detail="unknown event")

    message = template(req.order_id or "")
    # Forward to Hubtel
    sms_req = SmsRequest(phone=req.phone, message=message)
    return await send_sms(sms_req)


@app.post("/messages/send")
def send_message(msg: Message):
    key = f"{msg.company_id}:{msg.rider_id}"
    if key not in dialogs:
        dialogs[key] = []
    dialogs[key].append(msg.dict())
    return {"ok": True}


@app.get("/messages/thread/{company_id}/{rider_id}")
def get_thread(company_id: str, rider_id: str):
    key = f"{company_id}:{rider_id}"
    return {"messages": dialogs.get(key, [])}


@app.post("/alerts/send")
def send_alert(msg: Message):
    # For MVP, treat as a message with is_alert=True
    msg.is_alert = True
    return send_message(msg)
