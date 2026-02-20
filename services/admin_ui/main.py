import os
import time
import json
import random
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import httpx

# For demo: mock data sources (replace with real service calls in production)

app = FastAPI(title="Admin UI")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
APK_DIR = os.path.join(os.path.dirname(__file__), "apk")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/apk", StaticFiles(directory=APK_DIR), name="apk")

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8600")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:8200")


def get_token_from_request(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")
    return token


def proxy_get(request: Request, target_url: str):
    token = get_token_from_request(request)
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(target_url, headers=headers, params=dict(request.query_params))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type", "application/json"))


async def proxy_post(request: Request, target_url: str, body=None):
    token = get_token_from_request(request)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        if body is None:
            raw = await request.body()
            body = json.loads(raw) if raw else None
    except Exception:
        body = None
    try:
        with httpx.Client(timeout=15.0) as client:
            if body:
                r = client.post(target_url, headers=headers, json=body)
            else:
                r = client.post(target_url, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type", "application/json"))


# --- Page routes ---

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/login")
def login_page():
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))


@app.get("/booking")
def booking_page():
    return FileResponse(os.path.join(STATIC_DIR, "booking.html"))


@app.get("/superadmin")
def superadmin(request: Request):
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login?role=superadmin", status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "superadmin.html"))


@app.get("/merchant")
def merchant(request: Request):
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login?role=merchant", status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "merchant.html"))


@app.get("/company")
def company(request: Request):
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login?role=company", status_code=302)
    return FileResponse(os.path.join(STATIC_DIR, "company.html"))


# --- Auth endpoints ---

@app.post("/api/login")
def api_login(payload: dict, response: Response):
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/token", json={"username": username, "password": password})
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    data = r.json()
    response.set_cookie("access_token", data.get("access_token"), httponly=True, path="/")
    return {"ok": True, "role": data.get("role", ""), "username": data.get("username", username)}


@app.post("/api/logout")
def api_logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


# --- Company rider earnings endpoint ---
@app.get("/api/company/rider_earnings")
def company_rider_earnings(request: Request):
    company_id = request.query_params.get("company_id") or request.cookies.get("company_id") or "company-123"
    PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:8200")
    # Fetch all transactions and payouts for this company
    try:
        with httpx.Client(timeout=10.0) as client:
            r1 = client.get(f"{PAYMENT_SERVICE_URL}/transactions")
            r2 = client.get(f"{PAYMENT_SERVICE_URL}/admin/payouts", params={"company_id": company_id})
            r3 = client.get(f"{PAYMENT_SERVICE_URL}/companies/{company_id}/balance")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Payment service: {e}")
    txs = r1.json().get("transactions", []) if r1.status_code == 200 else []
    payouts = r2.json().get("payouts", []) if r2.status_code == 200 else []
    balance = r3.json().get("balance", 0) if r3.status_code == 200 else 0
    # Group earnings by rider if possible (if txs have rider_id)
    rider_earnings = {}
    for t in txs:
        rid = t.get("rider_id")
        if not rid:
            continue
        rider_earnings.setdefault(rid, {"total": 0, "txs": []})
        if t["type"] == "credit":
            rider_earnings[rid]["total"] += t.get("amount", 0)
        rider_earnings[rid]["txs"].append(t)
    return {
        "company_id": company_id,
        "balance": balance,
        "payouts": payouts,
        "rider_earnings": rider_earnings,
        "transactions": txs,
    }
# --- Company enroll rider endpoint (auto-gen password, links to company) ---
@app.post("/api/company/riders/enroll")
def company_enroll_rider(payload: dict, request: Request):
    """Register a new rider under this company with auto-generated password."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}

    # Get company info from /me
    try:
        with httpx.Client(timeout=10.0) as client:
            me_r = client.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
            if me_r.status_code != 200:
                raise HTTPException(status_code=401, detail="Auth failed")
            me = me_r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    if me.get("role") not in ("company_admin", "COMPANY_ADMIN"):
        raise HTTPException(status_code=403, detail="Only company admins")

    # Get the company record to find company.id
    try:
        with httpx.Client(timeout=10.0) as client:
            cr = client.get(f"{AUTH_SERVICE_URL}/company/commission", headers=headers)
            company_id = cr.json().get("company_id") if cr.status_code == 200 else None
    except Exception:
        company_id = None

    full_name = payload.get("full_name", "").strip()
    phone = payload.get("phone", "").strip()
    username = payload.get("username", "").strip()
    bike_id = payload.get("bike_id", "").strip()
    license_doc = payload.get("license_doc")  # base64 string

    if not full_name or not phone or not username or not bike_id:
        raise HTTPException(status_code=400, detail="full_name, phone, username, bike_id are required")
    if not license_doc:
        raise HTTPException(status_code=400, detail="ID or license document upload is required")

    # Auto-generate 5-digit passcode for rider login
    passcode = _generate_passcode()
    email = f"{username}@rider.packnet.local"

    reg_body = {
        "username": username,
        "email": email,
        "password": passcode,
        "phone": phone,
        "role": "rider",
        "bike_id": bike_id,
        "company_id": company_id,
        "license_doc": license_doc,
        "full_name": full_name,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/register", json=reg_body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    if r.status_code in (200, 201):
        return {"ok": True, "username": username, "passcode": passcode, "phone": phone, "full_name": full_name}
    else:
        detail = "Registration failed"
        try:
            detail = r.json().get("detail", detail)
        except Exception:
            pass
        raise HTTPException(status_code=r.status_code, detail=detail)


# --- Company: list riders with full details ---
@app.get("/api/company/riders")
def company_list_riders(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{AUTH_SERVICE_URL}/company/riders", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


# --- Company: suspend / ban / reactivate rider ---
@app.post("/api/company/riders/{user_id}/suspend")
def company_suspend_rider(user_id: str, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/users/{user_id}/suspend", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


@app.post("/api/company/riders/{user_id}/ban")
def company_ban_rider(user_id: str, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/users/{user_id}/ban", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


@app.post("/api/company/riders/{user_id}/reactivate")
def company_reactivate_rider(user_id: str, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/users/{user_id}/reactivate", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


# --- Company: commission management ---
@app.get("/api/company/commission")
def company_get_commission(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{AUTH_SERVICE_URL}/company/commission", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


@app.post("/api/company/commission")
def company_update_commission(payload: dict, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/company/commission", headers=headers, json=payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


# --- Company: revenue / balance ---
@app.get("/api/company/revenue")
def company_revenue(request: Request):
    """Get company balance, recent payments, and payout history."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")

    result = {"balance": 0, "total_revenue": 0, "total_payouts": 0, "payments": [], "payouts": [], "commission_pct": 15.0}
    try:
        with httpx.Client(timeout=10.0) as client:
            # Get company info for company_id
            cr = client.get(f"{AUTH_SERVICE_URL}/company/commission", headers=headers)
            company_id = ""
            if cr.status_code == 200:
                cd = cr.json()
                company_id = cd.get("company_id", "")
                result["commission_pct"] = cd.get("commission_pct", 15.0)

            # Balance from payment service
            if company_id:
                br = client.get(f"{PAYMENT_SERVICE_URL}/companies/{company_id}/balance")
                if br.status_code == 200:
                    result["balance"] = br.json().get("balance", 0)

            # Transactions
            tr = client.get(f"{PAYMENT_SERVICE_URL}/transactions")
            if tr.status_code == 200:
                txs = tr.json().get("transactions", [])
                result["payments"] = txs[:50]
                result["total_revenue"] = sum(t.get("amount", 0) for t in txs if t.get("type") == "credit")

            # Payouts
            if company_id:
                pr = client.get(f"{PAYMENT_SERVICE_URL}/admin/payouts", params={"company_id": company_id})
                if pr.status_code == 200:
                    payouts = pr.json().get("payouts", [])
                    result["payouts"] = payouts
                    result["total_payouts"] = sum(p.get("amount", 0) for p in payouts if p.get("status") == "COMPLETED")

            # Also get delivered orders revenue from order service
            or_r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
            if or_r.status_code == 200:
                orders = or_r.json() if isinstance(or_r.json(), list) else []
                delivered = [o for o in orders if o.get("status") == "DELIVERED"]
                result["total_revenue"] = round(sum(o.get("price_ghs", 0) for o in delivered), 2)
    except Exception:
        pass
    return result


# --- Company: request withdrawal (Hubtel) ---
@app.post("/api/company/withdraw")
def company_withdraw(payload: dict, request: Request):
    """Request a withdrawal via Hubtel."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    amount = payload.get("amount", 0)
    schedule = payload.get("schedule", "immediate")  # immediate, 3day, weekly

    # Get company_id
    try:
        with httpx.Client(timeout=10.0) as client:
            cr = client.get(f"{AUTH_SERVICE_URL}/company/commission", headers=headers)
            company_id = cr.json().get("company_id") if cr.status_code == 200 else None
    except Exception:
        company_id = None

    if not company_id:
        raise HTTPException(status_code=400, detail="Could not determine company")
    if not amount or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    payout_body = {"company_id": company_id, "amount": float(amount), "schedule": schedule}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{PAYMENT_SERVICE_URL}/payouts/request", json=payout_body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


# --- Company: in-app messaging ---
@app.post("/api/company/riders/{user_id}/message")
def company_send_message(user_id: str, payload: dict, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"rider_user_id": user_id, "message": payload.get("message", ""), "is_alert": payload.get("is_alert", False)}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/company/messages/send", headers=headers, json=body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


@app.get("/api/company/riders/{user_id}/messages")
def company_get_messages(user_id: str, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{AUTH_SERVICE_URL}/company/messages/{user_id}", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


# --- Company: live rider tracking (proxies to tracking service) ---
@app.get("/api/company/riders/{rider_id}/tracking")
def company_rider_tracking(rider_id: str, request: Request):
    """Get active tracking session for a rider from the tracking service."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    tracking_url = os.environ.get("TRACKING_SERVICE_URL", "http://localhost:8300")
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{tracking_url}/tracking/rider/{rider_id}", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


# --- Company dashboard endpoint (legacy) ---
@app.get("/api/company/dashboard")
def company_dashboard(request: Request):
    # For demo, get company_id from query param or cookie (in production, use JWT or session)
    company_id = request.query_params.get("company_id") or request.cookies.get("company_id") or "company-123"
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    TRACKING_SERVICE_URL = os.environ.get("TRACKING_SERVICE_URL", "http://localhost:8600")
    REVIEW_SERVICE_URL = os.environ.get("REVIEW_SERVICE_URL", "http://localhost:8700")
    RIDER_STATUS_URL = os.environ.get("RIDER_STATUS_URL", "http://localhost:8800")
    # Fetch company orders
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders/tenant", headers={"Authorization": "Bearer company_admin-token"})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order service: {e}")
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    orders = r.json() if isinstance(r.json(), list) else []
    # Filter orders for this company
    company_orders = [o for o in orders if o.get("assigned_company") == company_id]
    # Aggregate rider stats
    rider_stats = {}
    for o in company_orders:
        rider = (o.get("assigned_to") or {}).get("rider_id")
        if rider:
            rider_stats.setdefault(rider, {"completed": 0, "active": 0, "delivered": 0, "on_time": 0, "total": 0, "delivery_times": [], "order_ids": []})
            if o.get("status") == "DELIVERED":
                rider_stats[rider]["completed"] += 1
                rider_stats[rider]["delivered"] += 1
                # On-time delivery: delivered within 60 min of assignment (MVP logic)
                assigned_at = o.get("assigned_at")
                delivered_at = o.get("delivered_at")
                if assigned_at and delivered_at and delivered_at - assigned_at <= 3600:
                    rider_stats[rider]["on_time"] += 1
                if assigned_at and delivered_at:
                    rider_stats[rider]["delivery_times"].append(delivered_at - assigned_at)
                rider_stats[rider]["order_ids"].append(o.get("id"))
            elif o.get("status") == "ASSIGNED":
                rider_stats[rider]["active"] += 1
            rider_stats[rider]["total"] += 1
    # Fetch reviews for all riders
    rider_reviews = {}
    if REVIEW_SERVICE_URL:
        for rider_id in rider_stats:
            try:
                with httpx.Client(timeout=5.0) as client:
                    r = client.get(f"{REVIEW_SERVICE_URL}/reviews/rider/{rider_id}")
                    if r.status_code == 200:
                        data = r.json()
                        rider_reviews[rider_id] = data.get("reviews", [])
            except Exception:
                pass
    # Calculate average rating per rider
    for rider_id, stats in rider_stats.items():
        reviews = rider_reviews.get(rider_id, [])
        if reviews:
            stats["avg_rating"] = round(sum(r.get("rating", 0) for r in reviews) / len(reviews), 2)
            stats["num_ratings"] = len(reviews)
        else:
            stats["avg_rating"] = None
            stats["num_ratings"] = 0
        # On-time delivery rate
        stats["on_time_rate"] = round((stats["on_time"] / stats["delivered"] * 100) if stats["delivered"] else 0, 1)
    # Fetch status for all riders
    rider_statuses = {}
    if RIDER_STATUS_URL:
        for rider_id in rider_stats:
            try:
                with httpx.Client(timeout=3.0) as client:
                    r = client.get(f"{RIDER_STATUS_URL}/status/{rider_id}")
                    if r.status_code == 200:
                        data = r.json()
                        rider_statuses[rider_id] = data.get("status", "offline")
            except Exception:
                pass
    for rider_id, stats in rider_stats.items():
        stats["status"] = rider_statuses.get(rider_id, "offline")
    # Fetch live tracking for active riders
    active_riders = [r for r, s in rider_stats.items() if s["active"] > 0]
    live_locations = {}
    if active_riders and TRACKING_SERVICE_URL:
        for rider_id in active_riders:
            try:
                with httpx.Client(timeout=5.0) as client:
                    r = client.get(f"{TRACKING_SERVICE_URL}/tracking/rider/{rider_id}")
                    if r.status_code == 200:
                        data = r.json()
                        live_locations[rider_id] = data.get("last_location")
            except Exception:
                pass
    return {
        "company_id": company_id,
        "total_orders": len(company_orders),
        "active_orders": sum(1 for o in company_orders if o.get("status") == "ASSIGNED"),
        "completed_orders": sum(1 for o in company_orders if o.get("status") == "DELIVERED"),
        "riders": [{"rider_id": r, **s} for r, s in rider_stats.items()],
        "orders": company_orders,
        "active_riders": active_riders,
        "live_locations": live_locations,
    }
# --- Superadmin order/rider stats endpoint ---
@app.get("/api/admin/orders_stats")
def admin_orders_stats(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders/tenant", headers={"Authorization": "Bearer superadmin-token"})
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    orders = r.json() if isinstance(r.json(), list) else []
    total_orders = len(orders)
    assigned = sum(1 for o in orders if o.get("status") == "ASSIGNED")
    delivered = sum(1 for o in orders if o.get("status") == "DELIVERED")
    pending = sum(1 for o in orders if o.get("status") in ("OFFERED", "PENDING", "OFFERING"))
    recent = sorted(orders, key=lambda o: o.get("created_at", 0), reverse=True)[:10]
    return {
        "total_orders": total_orders,
        "assigned_orders": assigned,
        "delivered_orders": delivered,
        "pending_orders": pending,
        "recent_orders": recent,
    }

# --- Superadmin notifications/alerts endpoint (proxy to payment_service) ---
@app.get("/api/admin/alerts")
def admin_alerts(request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:8200")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{PAYMENT_SERVICE_URL}/admin/alerts")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()
# --- Superadmin user/role management endpoint ---
@app.get("/api/admin/users")
def admin_users(request: Request):
    """Proxy to auth service for real user list, wrapped in {users:[...]}."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{AUTH_SERVICE_URL}/users", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    users = r.json() if isinstance(r.json(), list) else []
    return {"users": users}


# --- Superadmin orders endpoint (for dashboard table) ---
@app.get("/api/admin/orders")
def admin_orders(request: Request):
    """Fetch all orders from order service, return with stats."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    orders = r.json() if isinstance(r.json(), list) else []
    delivered = sum(1 for o in orders if o.get("status") == "DELIVERED")
    revenue = round(sum(o.get("price_ghs", 0) for o in orders if o.get("status") == "DELIVERED"), 2)
    # Sort by created_at descending
    orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    return {"orders": orders, "delivered": delivered, "revenue": revenue}


# --- Superadmin riders endpoint ---
@app.get("/api/admin/riders")
def admin_riders(request: Request):
    """Get all riders from auth service users list."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    RIDER_STATUS_URL = os.environ.get("RIDER_STATUS_URL", "http://localhost:8800")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{AUTH_SERVICE_URL}/users", headers=headers)
            if r.status_code != 200:
                return {"riders": []}
            users = r.json() if isinstance(r.json(), list) else []
            riders = [u for u in users if u.get("role") in ("rider", "RIDER")]
            result = []
            for rider in riders:
                # Try to get online status
                status = "offline"
                try:
                    sr = client.get(f"{RIDER_STATUS_URL}/status/{rider.get('id')}", timeout=3.0)
                    if sr.status_code == 200:
                        status = sr.json().get("status", "offline")
                except Exception:
                    pass
                result.append({
                    "id": rider.get("id"),
                    "username": rider.get("username", ""),
                    "phone": rider.get("phone", ""),
                    "email": rider.get("email", ""),
                    "rating": rider.get("avg_rating"),
                    "completed": rider.get("completed_orders", 0),
                    "status": status,
                })
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"riders": result}
# --- Superadmin audit log endpoint ---
@app.get("/api/admin/audit_log")
def admin_audit_log(request: Request):
    # In production, fetch from DB or log service
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Here, return mock data for demo
    now = int(time.time())
    return {
        "log": [
            {"ts": now-60, "user": "superadmin", "action": "Approved merchant", "target": "merchant_123"},
            {"ts": now-120, "user": "superadmin", "action": "Edited merchant username", "target": "merchant_456"},
            {"ts": now-300, "user": "superadmin", "action": "Scheduled payout", "target": "company_789"},
            {"ts": now-600, "user": "superadmin", "action": "Banned user", "target": "user_321"},
        ]
    }

# --- Superadmin summary stats endpoint ---
@app.get("/api/admin/summary")
def admin_summary(request: Request):
    """Aggregate summary from real services."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    summary = {"last_updated": int(time.time())}
    try:
        headers = {"Authorization": f"Bearer {token}"}
        with httpx.Client(timeout=10.0) as client:
            # Get users from auth service
            try:
                r = client.get(f"{AUTH_SERVICE_URL}/users", headers=headers)
                if r.status_code == 200:
                    users = r.json() if isinstance(r.json(), list) else []
                    summary["total_merchants"] = sum(1 for u in users if u.get("role") in ("merchant", "MERCHANT"))
                    summary["active_merchants"] = sum(1 for u in users if u.get("role") in ("merchant", "MERCHANT") and u.get("is_active"))
                    summary["total_riders"] = sum(1 for u in users if u.get("role") in ("rider", "RIDER"))
                    summary["total_companies"] = sum(1 for u in users if u.get("role") in ("company_admin", "COMPANY_ADMIN"))
                    summary["total_users"] = len(users)
            except Exception:
                summary["total_merchants"] = 0
                summary["active_merchants"] = 0
                summary["total_riders"] = 0
                summary["total_companies"] = 0
            # Get order stats
            ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
            try:
                r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
                if r.status_code == 200:
                    orders = r.json() if isinstance(r.json(), list) else []
                    summary["total_orders"] = len(orders)
                    summary["delivered_orders"] = sum(1 for o in orders if o.get("status") == "DELIVERED")
                    summary["cancelled_orders"] = sum(1 for o in orders if o.get("status") == "CANCELLED")
                    summary["total_revenue"] = round(sum(o.get("price_ghs", 0) for o in orders if o.get("status") == "DELIVERED"), 2)
                    summary["cancelled_revenue"] = round(sum(o.get("price_ghs", 0) for o in orders if o.get("status") == "CANCELLED"), 2)
            except Exception:
                summary["total_orders"] = 0
                summary["total_revenue"] = 0.0
            # Get payout stats
            try:
                r = client.get(f"{PAYMENT_SERVICE_URL}/admin/payouts", headers=headers)
                if r.status_code == 200:
                    payouts = r.json() if isinstance(r.json(), list) else []
                    summary["total_payouts"] = len(payouts)
                    summary["failed_payouts"] = sum(1 for p in payouts if p.get("status") == "FAILED")
            except Exception:
                summary["total_payouts"] = 0
                summary["failed_payouts"] = 0
            summary["pending_merchants"] = 0
    except Exception:
        pass
    return summary


# --- Time-breakdown endpoint for orders ---
@app.get("/api/admin/orders/breakdown")
def admin_orders_breakdown(request: Request):
    """Order counts broken down by time periods."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    orders = r.json() if isinstance(r.json(), list) else []
    now = datetime.utcnow()
    periods = {"1h": 1, "4h": 4, "6h": 6, "1d": 24, "3d": 72, "monthly": 720}
    result = {}
    for label, hours in periods.items():
        cutoff = now - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        count = sum(1 for o in orders if (o.get("created_at") or "") >= cutoff_str)
        result[label] = count
    result["total"] = len(orders)
    return result


# --- Time-breakdown endpoint for delivered orders ---
@app.get("/api/admin/delivered/breakdown")
def admin_delivered_breakdown(request: Request):
    """Delivered order counts broken down by time periods."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    orders = r.json() if isinstance(r.json(), list) else []
    delivered = [o for o in orders if o.get("status") == "DELIVERED"]
    now = datetime.utcnow()
    periods = {"1h": 1, "4h": 4, "6h": 6, "1d": 24, "3d": 72, "monthly": 720}
    result = {}
    for label, hours in periods.items():
        cutoff = now - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        count = sum(1 for o in delivered if (o.get("delivered_at") or o.get("created_at") or "") >= cutoff_str)
        result[label] = count
    result["total"] = len(delivered)
    return result


# --- Time-breakdown endpoint for revenue ---
@app.get("/api/admin/revenue/breakdown")
def admin_revenue_breakdown(request: Request):
    """Revenue broken down by time periods."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    orders = r.json() if isinstance(r.json(), list) else []
    delivered = [o for o in orders if o.get("status") == "DELIVERED"]
    now = datetime.utcnow()
    periods = {"1h": 1, "4h": 4, "6h": 6, "1d": 24, "3d": 72, "monthly": 720}
    result = {}
    for label, hours in periods.items():
        cutoff = now - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        rev = round(sum(o.get("price_ghs", 0) for o in delivered if (o.get("delivered_at") or o.get("created_at") or "") >= cutoff_str), 2)
        result[label] = rev
    result["total"] = round(sum(o.get("price_ghs", 0) for o in delivered), 2)
    return result


# --- Superadmin: Platform Financial Overview ---
@app.get("/api/admin/financials")
def admin_financials(request: Request):
    """Comprehensive financial data: revenue, commissions, payouts, cancelled orders."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")

    result = {
        "total_revenue": 0, "total_commissions": 0, "total_payouts": 0,
        "pending_payouts": 0, "failed_payouts": 0,
        "cancelled_orders": 0, "cancelled_revenue_lost": 0,
        "transactions": [], "payouts": [], "cancelled": [],
        "companies_summary": [],
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            # Orders
            try:
                r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
                if r.status_code == 200:
                    orders = r.json() if isinstance(r.json(), list) else []
                    delivered = [o for o in orders if o.get("status") == "DELIVERED"]
                    cancelled = [o for o in orders if o.get("status") == "CANCELLED"]
                    result["total_revenue"] = round(sum(o.get("price_ghs", 0) for o in delivered), 2)
                    result["cancelled_orders"] = len(cancelled)
                    result["cancelled_revenue_lost"] = round(sum(o.get("price_ghs", 0) for o in cancelled), 2)
                    cancelled.sort(key=lambda o: o.get("created_at", ""), reverse=True)
                    result["cancelled"] = cancelled[:30]
            except Exception:
                pass

            # Transactions from payment service
            try:
                tr = client.get(f"{PAYMENT_SERVICE_URL}/transactions")
                if tr.status_code == 200:
                    txs = tr.json().get("transactions", [])
                    result["transactions"] = txs[:50]
            except Exception:
                pass

            # Payouts from payment service
            try:
                pr = client.get(f"{PAYMENT_SERVICE_URL}/admin/payouts")
                if pr.status_code == 200:
                    payouts_data = pr.json()
                    payouts = payouts_data.get("payouts", []) if isinstance(payouts_data, dict) else (payouts_data if isinstance(payouts_data, list) else [])
                    result["payouts"] = payouts[:50]
                    result["total_payouts"] = round(sum(p.get("amount", 0) for p in payouts if p.get("status") == "COMPLETED"), 2)
                    result["pending_payouts"] = sum(1 for p in payouts if p.get("status") in ("REQUESTED", "PENDING"))
                    result["failed_payouts"] = sum(1 for p in payouts if p.get("status") == "FAILED")
            except Exception:
                pass

            # Companies with rider counts and commission
            try:
                r = client.get(f"{AUTH_SERVICE_URL}/users", headers=headers)
                if r.status_code == 200:
                    users = r.json() if isinstance(r.json(), list) else []
                    companies = [u for u in users if u.get("role") in ("company_admin", "COMPANY_ADMIN")]
                    riders = [u for u in users if u.get("role") in ("rider", "RIDER")]
                    # For now, count all riders per company (we don't have company linkage in user list)
                    # Show total rider count
                    for comp in companies:
                        result["companies_summary"].append({
                            "id": comp.get("id"),
                            "username": comp.get("username", ""),
                            "email": comp.get("email", ""),
                            "is_active": comp.get("is_active", True),
                            "is_suspended": comp.get("is_suspended", False),
                            "is_banned": comp.get("is_banned", False),
                            "created_at": comp.get("created_at", ""),
                        })
                    result["total_rider_count"] = len(riders)
            except Exception:
                pass

            # Estimate platform commissions (platform keeps ~15% default)
            result["total_commissions"] = round(result["total_revenue"] * 0.15, 2)
    except Exception:
        pass
    return result


# --- Superadmin: cancelled orders detail ---
@app.get("/api/admin/cancelled")
def admin_cancelled_orders(request: Request):
    """Get all cancelled orders with breakdown."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        return {"cancelled": [], "total": 0, "total_lost": 0}
    orders = r.json() if isinstance(r.json(), list) else []
    cancelled = [o for o in orders if o.get("status") == "CANCELLED"]
    now = datetime.utcnow()
    periods = {"1h": 1, "4h": 4, "6h": 6, "1d": 24, "3d": 72, "monthly": 720}
    breakdown = {}
    for label, hours in periods.items():
        cutoff = (now - timedelta(hours=hours)).isoformat()
        breakdown[label] = sum(1 for o in cancelled if (o.get("created_at") or "") >= cutoff)
    breakdown["total"] = len(cancelled)
    cancelled.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    return {
        "cancelled": cancelled[:30],
        "total": len(cancelled),
        "total_lost": round(sum(o.get("price_ghs", 0) for o in cancelled), 2),
        "breakdown": breakdown,
    }


# --- Public Booking page route ---
@app.get("/book")
def booking_page():
    return FileResponse(os.path.join(STATIC_DIR, "booking.html"))


# --- Public Booking API proxy to booking-service ---
BOOKING_SERVICE_URL = os.environ.get("BOOKING_SERVICE_URL", "http://localhost:8100")


@app.post("/api/book")
def api_book(payload: dict):
    """Proxy booking request to booking-service. Public endpoint — no auth required."""
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{BOOKING_SERVICE_URL}/book", json=payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Booking service unavailable: {e}")
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


@app.get("/api/maps-config")
def maps_config():
    """Return Google Maps API key for client-side use (public endpoint)."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    return {"api_key": key, "has_key": bool(key)}


# --- Rider detail endpoint ---
@app.get("/api/admin/rider/{rider_id}/detail")
def admin_rider_detail(rider_id: str, request: Request):
    """Get detailed info about a specific rider."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    RIDER_STATUS_URL = os.environ.get("RIDER_STATUS_URL", "http://localhost:8800")
    REVIEW_SERVICE_URL = os.environ.get("REVIEW_SERVICE_URL", "http://localhost:8700")
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    detail = {"id": rider_id}
    try:
        with httpx.Client(timeout=10.0) as client:
            # Get user info
            r = client.get(f"{AUTH_SERVICE_URL}/users", headers=headers)
            if r.status_code == 200:
                users = r.json() if isinstance(r.json(), list) else []
                rider = next((u for u in users if u.get("id") == rider_id), None)
                if rider:
                    detail["username"] = rider.get("username", "")
                    detail["email"] = rider.get("email", "")
                    detail["phone"] = rider.get("phone", "")
                    detail["role"] = rider.get("role", "")
                    detail["is_active"] = rider.get("is_active", True)
                    detail["created_at"] = rider.get("created_at", "")
                    # Find linked company
                    companies = [u for u in users if u.get("role") in ("company_admin", "COMPANY_ADMIN")]
                    detail["company"] = companies[0].get("username", "Unknown") if companies else "Independent"
            # Get rider status
            try:
                sr = client.get(f"{RIDER_STATUS_URL}/status/{rider_id}", timeout=3.0)
                if sr.status_code == 200:
                    detail["status"] = sr.json().get("status", "offline")
                    detail["last_seen"] = sr.json().get("last_updated", "")
                else:
                    detail["status"] = "offline"
            except Exception:
                detail["status"] = "offline"
            # Get rider orders
            try:
                r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
                if r.status_code == 200:
                    orders = r.json() if isinstance(r.json(), list) else []
                    rider_orders = [o for o in orders if o.get("assigned_rider_id") == rider_id]
                    detail["total_orders"] = len(rider_orders)
                    detail["completed_orders"] = sum(1 for o in rider_orders if o.get("status") == "DELIVERED")
                    detail["active_orders"] = sum(1 for o in rider_orders if o.get("status") in ("ASSIGNED", "IN_TRANSIT"))
                    detail["total_revenue"] = round(sum(o.get("price_ghs", 0) for o in rider_orders if o.get("status") == "DELIVERED"), 2)
                    # Recent orders (last 5)
                    rider_orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
                    detail["recent_orders"] = rider_orders[:5]
            except Exception:
                detail["total_orders"] = 0
                detail["completed_orders"] = 0
                detail["recent_orders"] = []
            # Get reviews
            try:
                r = client.get(f"{REVIEW_SERVICE_URL}/reviews/rider/{rider_id}", timeout=5.0)
                if r.status_code == 200:
                    reviews = r.json().get("reviews", [])
                    if reviews:
                        detail["avg_rating"] = round(sum(rv.get("rating", 0) for rv in reviews) / len(reviews), 2)
                        detail["review_count"] = len(reviews)
                    else:
                        detail["avg_rating"] = None
                        detail["review_count"] = 0
                else:
                    detail["avg_rating"] = None
                    detail["review_count"] = 0
            except Exception:
                detail["avg_rating"] = None
                detail["review_count"] = 0
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return detail


# --- Merchant admin proxies ---

@app.get("/api/merchants/pending")
def api_merchants_pending(request: Request):
    """Return pending merchants. Auth service may not have this yet, so handle gracefully."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{AUTH_SERVICE_URL}/merchants/pending", headers=headers)
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return {"pending": []}


@app.get("/api/companies/pending")
def api_companies_pending(request: Request):
    """Return pending companies. Auth service may not have this yet, so handle gracefully."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{AUTH_SERVICE_URL}/companies/pending", headers=headers)
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return {"pending": []}


@app.post("/api/companies/{cid}/approve")
async def api_company_approve(cid: str, request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/companies/{cid}/approve")


@app.post("/api/companies/batch_approve")
async def api_companies_batch_approve(request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/companies/batch_approve")


# Edit merchant details (username, store_address)
@app.post("/api/merchants/{mid}/edit")
async def api_merchant_edit(mid: str, payload: dict, request: Request):
    # Proxy to auth service or merchant service (replace with real endpoint)
    # For demo, just return ok
    # In production, validate fields and forward to real backend
    allowed_fields = {"username", "store_address"}
    update = {k: v for k, v in payload.items() if k in allowed_fields}
    if not update:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    # Example: forward to AUTH_SERVICE_URL/merchants/{mid}/edit
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/merchants/{mid}/edit", json=update)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return {"ok": True}


@app.post("/api/merchants/{mid}/approve")
async def api_merchant_approve(mid: str, request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/merchants/{mid}/approve")


@app.post("/api/merchants/batch_approve")
async def api_merchants_batch_approve(request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/merchants/batch_approve")


# User management (suspend/ban)
@app.post("/api/users/{uid}/suspend")
async def api_user_suspend(uid: str, request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/users/{uid}/suspend")


@app.post("/api/users/{uid}/unsuspend")
async def api_user_unsuspend(uid: str, request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/users/{uid}/reactivate")


@app.post("/api/users/{uid}/ban")
async def api_user_ban(uid: str, request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/users/{uid}/ban")


@app.post("/api/users/{uid}/unban")
async def api_user_unban(uid: str, request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/users/{uid}/reactivate")

# Rider passcode login (for mobile app)
@app.post("/api/rider/passcode-login")
async def api_rider_passcode_login(request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/rider/passcode-login")

# Rider change passcode
@app.post("/api/rider/change-passcode")
async def api_rider_change_passcode(request: Request):
    return await proxy_post(request, f"{AUTH_SERVICE_URL}/rider/change-passcode")


# --- Enrollment endpoints (superadmin creates accounts) ---

def _generate_password(length=10):
    chars = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(chars) for _ in range(length))


def _generate_passcode():
    """Generate a 5-digit numeric passcode for riders."""
    return str(random.randint(10000, 99999))


def _generate_username(name: str, role_prefix: str):
    slug = name.lower().replace(" ", "_").replace("-", "_")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")[:20]
    suffix = str(random.randint(10, 99))
    return f"{role_prefix}_{slug}_{suffix}"


@app.post("/api/admin/enroll/company")
def admin_enroll_company(payload: dict, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Validate required fields
    company_name = payload.get("company_name", "").strip()
    contact_person = payload.get("contact_person", "").strip()
    phone = payload.get("phone", "").strip()
    email = payload.get("email", "").strip()
    address = payload.get("address", "").strip()
    num_bikes = payload.get("num_bikes", 0)
    coverage = payload.get("coverage_location", "").strip()
    if not company_name or not contact_person or not phone or not email:
        raise HTTPException(status_code=400, detail="company_name, contact_person, phone and email are required")
    # Auto-generate credentials
    username = _generate_username(company_name, "co")
    password = _generate_password()
    # Register via auth service
    reg_payload = {
        "username": username,
        "email": email,
        "password": password,
        "phone": phone,
        "role": "company_admin",
        "company_name": company_name,
        "contact_person": contact_person,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/register", json=reg_payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Auth service error: {e}")
    if r.status_code not in (200, 201):
        detail = r.text
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            pass
        raise HTTPException(status_code=r.status_code, detail=f"Registration failed: {detail}")
    return {
        "ok": True,
        "username": username,
        "password": password,
        "company_name": company_name,
        "role": "company_admin",
        "message": f"Rider company '{company_name}' enrolled successfully"
    }


@app.post("/api/admin/enroll/merchant")
def admin_enroll_merchant(payload: dict, request: Request):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Validate required fields
    business_name = payload.get("business_name", "").strip()
    owner_name = payload.get("owner_name", "").strip()
    phone = payload.get("phone", "").strip()
    email = payload.get("email", "").strip()
    address = payload.get("address", "").strip()
    business_type = payload.get("business_type", "").strip()
    avg_daily_orders = payload.get("avg_daily_orders", 0)
    if not business_name or not owner_name or not phone or not email:
        raise HTTPException(status_code=400, detail="business_name, owner_name, phone and email are required")
    # Auto-generate credentials
    username = _generate_username(business_name, "merch")
    password = _generate_password()
    # Register via auth service
    reg_payload = {
        "username": username,
        "email": email,
        "password": password,
        "phone": phone,
        "role": "merchant",
        "store_name": business_name,
        "momo_number": phone,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(f"{AUTH_SERVICE_URL}/register", json=reg_payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Auth service error: {e}")
    if r.status_code not in (200, 201):
        detail = r.text
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            pass
        raise HTTPException(status_code=r.status_code, detail=f"Registration failed: {detail}")
    return {
        "ok": True,
        "username": username,
        "password": password,
        "business_name": business_name,
        "role": "merchant",
        "message": f"Merchant '{business_name}' enrolled successfully"
    }


# Payment admin proxies
@app.get("/api/admin/payouts")
def api_payouts(request: Request):
    return proxy_get(request, f"{PAYMENT_SERVICE_URL}/admin/payouts")


@app.post("/api/admin/payouts/{pid}/retry")
async def api_payout_retry(pid: str, request: Request):
    return await proxy_post(request, f"{PAYMENT_SERVICE_URL}/admin/payouts/{pid}/retry")


@app.post("/api/admin/payouts/{pid}/cancel")
async def api_payout_cancel(pid: str, request: Request):
    return await proxy_post(request, f"{PAYMENT_SERVICE_URL}/admin/payouts/{pid}/cancel")


@app.post("/api/admin/payouts/{pid}/reconcile")
async def api_payout_reconcile(pid: str, request: Request):
    return await proxy_post(request, f"{PAYMENT_SERVICE_URL}/admin/payouts/{pid}/reconcile")


@app.get("/api/transactions")
def api_transactions(request: Request):
    return proxy_get(request, f"{PAYMENT_SERVICE_URL}/transactions")


@app.get("/api/admin/webhooks/log")
def api_webhooks_log(request: Request):
    return proxy_get(request, f"{PAYMENT_SERVICE_URL}/admin/webhooks/log")


@app.get("/api/reconciliation/export")
def api_export(request: Request):
    return proxy_get(request, f"{PAYMENT_SERVICE_URL}/admin/reconciliation/export")


# --- Company dashboard v2 (auth-based) ---
@app.get("/api/company/dashboard_v2")
def company_dashboard_v2(request: Request):
    """Company dashboard using auth cookie instead of manual company_id."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    RIDER_STATUS_URL = os.environ.get("RIDER_STATUS_URL", "http://localhost:8800")
    result = {"company_name": "", "company_id": "", "commission_pct": 15.0,
              "total_riders": 0, "total_orders": 0, "active_orders": 0,
              "completed_orders": 0, "total_revenue": 0, "balance": 0,
              "riders": [], "orders": []}
    try:
        with httpx.Client(timeout=10.0) as client:
            # Get current user info (company_admin)
            try:
                r = client.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
                if r.status_code == 200:
                    me = r.json()
                    result["company_name"] = me.get("username", "Company")
                    result["company_id"] = me.get("id", "")
            except Exception:
                pass
            # Get commission settings
            try:
                cr = client.get(f"{AUTH_SERVICE_URL}/company/commission", headers=headers)
                if cr.status_code == 200:
                    cd = cr.json()
                    result["commission_pct"] = cd.get("commission_pct", 15.0)
                    result["company_id"] = cd.get("company_id", result["company_id"])
                    result["company_name"] = cd.get("company_name", result["company_name"])
            except Exception:
                pass
            # Get company riders (filtered by company)
            try:
                r = client.get(f"{AUTH_SERVICE_URL}/company/riders", headers=headers)
                if r.status_code == 200:
                    riders = r.json() if isinstance(r.json(), list) else []
                    result["total_riders"] = len(riders)
                    result["riders"] = riders
            except Exception:
                pass
            # Get balance from payment service
            if result["company_id"]:
                try:
                    br = client.get(f"{PAYMENT_SERVICE_URL}/companies/{result['company_id']}/balance")
                    if br.status_code == 200:
                        result["balance"] = br.json().get("balance", 0)
                except Exception:
                    pass
            # Get orders
            try:
                r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
                if r.status_code == 200:
                    orders = r.json() if isinstance(r.json(), list) else []
                    result["total_orders"] = len(orders)
                    result["active_orders"] = sum(1 for o in orders if o.get("status") in ("ASSIGNED", "IN_TRANSIT"))
                    result["completed_orders"] = sum(1 for o in orders if o.get("status") == "DELIVERED")
                    result["total_revenue"] = round(sum(o.get("price_ghs", 0) for o in orders if o.get("status") == "DELIVERED"), 2)
                    orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
                    result["orders"] = orders[:20]
            except Exception:
                pass
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result

# --- Merchant Dashboard & Order Proxy ---

@app.get("/api/merchant/dashboard")
async def merchant_dashboard(request: Request):
    """Return merchant profile, order stats, and recent orders."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")

    result = {
        "store_name": "",
        "store_address": "",
        "total_orders": 0,
        "pending": 0,
        "assigned": 0,
        "in_transit": 0,
        "delivered": 0,
        "cancelled": 0,
        "orders": [],
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            # Get user profile from auth service
            me = client.get(f"{AUTH_SERVICE_URL}/me", headers=headers)
            if me.status_code == 200:
                u = me.json()
                result["username"] = u.get("username", "")
                result["store_name"] = u.get("store_name", "")
                result["store_address"] = u.get("store_address", "")

            # Get merchant orders from order service
            r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers)
            if r.status_code == 200:
                orders = r.json() if isinstance(r.json(), list) else []
                result["total_orders"] = len(orders)
                result["pending"] = sum(1 for o in orders if o.get("status") == "PENDING")
                result["assigned"] = sum(1 for o in orders if o.get("status") == "ASSIGNED")
                result["in_transit"] = sum(1 for o in orders if o.get("status") in ("IN_TRANSIT", "PICKED_UP"))
                result["delivered"] = sum(1 for o in orders if o.get("status") == "DELIVERED")
                result["cancelled"] = sum(1 for o in orders if o.get("status") == "CANCELLED")
                orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
                result["orders"] = orders
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result


@app.post("/api/merchant/orders/create")
async def merchant_create_order(payload: dict, request: Request):
    """Proxy order creation through admin-ui so frontend never talks to microservices directly."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    PAYMENT_SERVICE_URL_LOCAL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:8200")

    # Step 1: Create a manual/placeholder payment so order service accepts it
    pay_payload = {
        "amount": payload.get("price_ghs", 10),
        "currency": "GHS",
        "phone": payload.get("recipient_phone", "0000000000"),
        "payment_method": "momo",
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            pr = client.post(f"{PAYMENT_SERVICE_URL_LOCAL}/payments/initiate", headers=headers, json=pay_payload)
            if pr.status_code in (200, 201):
                payment_id = pr.json().get("id") or pr.json().get("payment_id", "manual")
            else:
                payment_id = "manual"

            # Step 2: Create the order
            order_payload = {
                "payment_id": payment_id,
                "merchant_id": None,
                "pickup_address": payload.get("pickup_address", "Store"),
                "pickup_lat": float(payload.get("pickup_lat", 0)),
                "pickup_lng": float(payload.get("pickup_lng", 0)),
                "dropoff_address": payload.get("dropoff_address", ""),
                "dropoff_lat": float(payload.get("dropoff_lat", 0)),
                "dropoff_lng": float(payload.get("dropoff_lng", 0)),
                "distance_km": float(payload.get("distance_km", 5)),
                "eta_min": int(payload.get("eta_min", 30)),
                "price_ghs": float(payload.get("price_ghs", 10)),
            }
            r = client.post(f"{ORDER_SERVICE_URL}/orders/create", headers=headers, json=order_payload)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))


@app.get("/api/merchant/orders")
async def merchant_list_orders(request: Request):
    """Proxy order listing for merchant."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    headers = {"Authorization": f"Bearer {token}"}
    ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(f"{ORDER_SERVICE_URL}/orders", headers=headers,
                           params=dict(request.query_params))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type", "application/json"))