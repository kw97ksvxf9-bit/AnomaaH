import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Booking Service")

GOOGLE_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL")

@app.get("/health")
def health():
    return {"status": "ok", "service": "booking"}


class BookingRequest(BaseModel):
    pickup_address: str
    pickup_lat: float
    pickup_lng: float
    dropoff_address: str
    dropoff_lat: float
    dropoff_lng: float
    phone: str


class BookingResponse(BaseModel):
    status: str
    distance_km: float
    eta_min: int
    price_ghs: float
    payment_required: bool
    payment_payload: Optional[dict]


async def google_distance_eta(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{pickup_lat},{pickup_lng}",
        "destinations": f"{dropoff_lat},{dropoff_lng}",
        "key": GOOGLE_API_KEY,
        "mode": "driving",
        "departure_time": "now",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        try:
            elem = data["rows"][0]["elements"][0]
            distance_m = elem["distance"]["value"]
            duration_s = elem["duration"]["value"]
            return distance_m / 1000.0, int(duration_s / 60)
        except Exception:
            raise HTTPException(status_code=502, detail="Invalid response from Google Maps")


def stub_distance_and_eta(pickup, dropoff):
    dx = pickup[0] - dropoff[0]
    dy = pickup[1] - dropoff[1]
    dist_km = ((dx * dx + dy * dy) ** 0.5) * 111
    eta_min = max(10, int(dist_km / 0.5 * 10))
    return dist_km, eta_min


def compute_price(distance_km: float) -> float:
    """GHS 5 base fare + GHS 1.50 per km, minimum GHS 10"""
    base   = 5.0
    per_km = 1.5
    return round(max(10.0, base + distance_km * per_km), 2)


@app.post("/book", response_model=BookingResponse)
async def book(req: BookingRequest):
    pickup = (req.pickup_lat, req.pickup_lng)
    dropoff = (req.dropoff_lat, req.dropoff_lng)

    # Try Google Maps first, fallback to stub
    try:
        if GOOGLE_API_KEY:
            distance_km, eta_min = await google_distance_eta(*pickup, *dropoff)
        else:
            raise Exception("no google key")
    except Exception:
        distance_km, eta_min = stub_distance_and_eta(pickup, dropoff)

    price_ghs = compute_price(distance_km)

    payment_payload = None
    if PAYMENT_SERVICE_URL:
        # initiate payment with external payment service
        payload = {
            "amount": price_ghs,
            "currency": "GHS",
            "phone": req.phone,
            "metadata": {
                "pickup_address": req.pickup_address,
                "dropoff_address": req.dropoff_address,
                "timestamp": int(time.time()),
            },
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(f"{PAYMENT_SERVICE_URL}/payments/initiate", json=payload)
                r.raise_for_status()
                payment_payload = r.json()
                # notify user that booking/payment initiation is created
                phone = req.phone
                payment_id = payment_payload.get("payment_id") if isinstance(payment_payload, dict) else None
                try:
                    await notify_event(phone, "order_placed", payment_id)
                except Exception:
                    pass
        except Exception:
            # If payment service is down, still return booking details and a client-side retry option
            payment_payload = {"error": "payment_service_unavailable"}
    else:
        # No payment service configured; return a mock payment link (for dev)
        mock_token = f"mock_{int(time.time())}"
        payment_payload = {"provider": "mock", "payment_url": f"https://pay.example.local/{mock_token}", "token": mock_token}

    return {
        "status": "ok",
        "distance_km": round(distance_km, 2),
        "eta_min": eta_min,
        "price_ghs": price_ghs,
        "payment_required": True,
        "payment_payload": payment_payload,
    }


async def notify_event(phone: str, event: str, order_id: Optional[str] = None):
    if not NOTIFICATION_SERVICE_URL:
        return {"ok": False, "reason": "no_notification_service"}
    payload = {"phone": phone, "event": event, "order_id": order_id}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{NOTIFICATION_SERVICE_URL}/notify/event", json=payload)
            r.raise_for_status()
            return r.json()
    except Exception:
        return {"ok": False, "reason": "notify_failed"}
