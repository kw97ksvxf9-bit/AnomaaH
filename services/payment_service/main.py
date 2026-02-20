import threading
import os
import sys
import uuid
import time
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Header, Depends, status
from typing import Optional
import jwt
from pydantic import BaseModel
import httpx
import hmac
import hashlib
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database import get_db, engine, Base
from shared.models import Payment, PaymentStatus
from shared.webhooks import verify_hubtel_webhook, webhook_audit, WebhookEvent

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payment Service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "payment"}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory alert log (thread-safe)
ALERT_LOG = []
ALERT_LOCK = threading.Lock()

def log_alert(level, msg):
    now = int(time.time())
    with ALERT_LOCK:
        ALERT_LOG.append({"ts": now, "level": level, "msg": msg})
        if len(ALERT_LOG) > 100:
            ALERT_LOG.pop(0)

PLATFORM_FEE_GHS = float(os.environ.get("PLATFORM_FEE_GHS", "3"))

# SMS credentials (shared with notification service)
HUBTEL_CLIENT_ID = os.environ.get("HUBTEL_CLIENT_ID")
HUBTEL_CLIENT_SECRET = os.environ.get("HUBTEL_CLIENT_SECRET")

# Payment collection credentials (Hubtel Receive Money dashboard)
HUBTEL_PAYMENT_CLIENT_ID     = os.environ.get("HUBTEL_PAYMENT_CLIENT_ID") or HUBTEL_CLIENT_ID
HUBTEL_PAYMENT_CLIENT_SECRET = os.environ.get("HUBTEL_PAYMENT_CLIENT_SECRET") or HUBTEL_CLIENT_SECRET
HUBTEL_MERCHANT_ACCOUNT      = os.environ.get("HUBTEL_MERCHANT_ACCOUNT") or HUBTEL_PAYMENT_CLIENT_ID
HUBTEL_CALLBACK_URL          = os.environ.get("HUBTEL_CALLBACK_URL", "http://localhost:8200")
HUBTEL_RECEIVE_MONEY_URL     = os.environ.get(
    "HUBTEL_RECEIVE_MONEY_URL",
    "https://api.hubtel.com/v1/merchantaccount/merchants/{account}/receive/mobilemoney"
)

HUBTEL_PAYOUT_URL = os.environ.get("HUBTEL_PAYOUT_URL")
HUBTEL_PAYOUT_API_KEY = os.environ.get("HUBTEL_PAYOUT_API_KEY")
HUBTEL_WEBHOOK_SECRET = os.environ.get("HUBTEL_WEBHOOK_SECRET")
HUBTEL_SIGNATURE_HEADER = os.environ.get("HUBTEL_SIGNATURE_HEADER", "X-Hubtel-Signature")
JWT_SECRET = os.environ.get("JWT_SECRET", os.environ.get("SECRET_KEY", "replace-me"))

# Service URLs
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:8400")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8500")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")
PAYPAL_ACCESS_TOKEN = os.environ.get("PAYPAL_ACCESS_TOKEN", "")

# ── Hubtel helper utilities ──────────────────────────────────────────────────
_MTN_PREFIXES       = {"024","054","055","059","025","068","069"}
_VODAFONE_PREFIXES  = {"020","050"}
_AIRTELTIGO_PREFIXES= {"026","027","056","057"}

def _gh_phone(phone: str) -> str:
    """Normalise a Ghana phone to 233XXXXXXXXX format."""
    p = phone.strip().replace("+","").replace(" ","").replace("-","")
    if p.startswith("233"):
        return p
    if p.startswith("0"):
        return "233" + p[1:]
    return p

def _detect_channel(phone_233: str) -> str:
    """Detect Ghana MoMo network from a 233XXXXXXXXX number."""
    local_prefix = "0" + phone_233[3:6]
    if local_prefix in _MTN_PREFIXES:
        return "mtn-gh"
    if local_prefix in _VODAFONE_PREFIXES:
        return "vodafone-gh"
    if local_prefix in _AIRTELTIGO_PREFIXES:
        return "airteltigo-gh"
    return "mtn-gh"  # default for unknown prefixes
JWT_ALGO = "HS256"


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="missing authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="invalid authorization header")
    token = authorization.split(None, 1)[1]
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")
    return {"user_id": data.get("sub"), "role": data.get("role"), "company_id": data.get("company_id")}

# In-memory store for MVP
payouts = {}
# In-memory store for MVP
payments = {}
payouts = {}
# simple in-memory ledger: company_id -> available balance (in GHS integer units)
company_balances = {}

# simple transaction log for auditing (in-memory for MVP)
transactions = []


class InitiateRequest(BaseModel):
    amount: int
    currency: str = "GHS"
    phone: Optional[str] = None
    metadata: dict = {}


class PayoutRequest(BaseModel):
    company_id: str
    amount: int
    schedule: str  # immediate|3day|weekly


@app.post("/payments/initiate")
async def initiate(req: InitiateRequest):
    payment_id = str(uuid.uuid4())
    # flat platform fee in GHS (integer units)
    platform_fee = int(PLATFORM_FEE_GHS)
    merchant_amount = req.amount - platform_fee

    # if phone not provided but merchant_id available, try to fetch merchant momo
    if (not req.phone) and req.metadata and req.metadata.get("merchant_id") and os.environ.get("AUTH_SERVICE_URL"):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{os.environ.get('AUTH_SERVICE_URL')}/merchants/{req.metadata.get('merchant_id')}")
                if r.status_code == 200:
                    jr = r.json()
                    momo = jr.get("momo_number")
                    if momo:
                        req.phone = momo
        except Exception:
            pass

    # ── Record payment in memory first ─────────────────────────────────────
    payments[payment_id] = {
        "id": payment_id,
        "status": "CREATED",
        "amount": req.amount,
        "currency": req.currency,
        "phone": req.phone,
        "metadata": req.metadata,
        "platform_fee": platform_fee,
        "merchant_amount": merchant_amount,
    }

    # ── Call real Hubtel Receive Money API (if credentials configured) ──────
    # Falls back to mock_pay URL when running locally without live credentials.
    payment_url = (
        f"http://{os.environ.get('API_HOST','localhost')}:{os.environ.get('API_PORT','8200')}"
        f"/payments/mock_pay/{payment_id}"
    )
    hubtel_ref = None

    if HUBTEL_PAYMENT_CLIENT_ID and HUBTEL_PAYMENT_CLIENT_SECRET and req.phone:
        try:
            phone_233  = _gh_phone(req.phone)
            channel    = _detect_channel(phone_233)
            hub_url    = HUBTEL_RECEIVE_MONEY_URL.format(account=HUBTEL_MERCHANT_ACCOUNT)
            cb_url     = f"{HUBTEL_CALLBACK_URL.rstrip('/')}/payments/webhook"
            amount_str = f"{float(req.amount):.2f}"

            hub_payload = {
                "CustomerMsisdn":    phone_233,
                "Channel":           channel,
                "Amount":            amount_str,
                "PrimaryCallbackUrl": cb_url,
                "Description":       req.metadata.get("description", "ANOMAAH Delivery"),
                "ClientReference":   payment_id,
            }

            logger.info(f"Hubtel Receive Money → {phone_233} {channel} GHS {amount_str}")
            async with httpx.AsyncClient(
                auth=(HUBTEL_PAYMENT_CLIENT_ID, HUBTEL_PAYMENT_CLIENT_SECRET),
                timeout=20.0
            ) as client:
                hr = await client.post(hub_url, json=hub_payload)
                hr_data = hr.json() if hr.content else {}
                logger.info(f"Hubtel response {hr.status_code}: {hr_data}")

            if hr.status_code in (200, 201, 202):
                # Hubtel accepted — MoMo prompt sent to customer
                hubtel_ref   = hr_data.get("Data", {}).get("TransactionId") or hr_data.get("TransactionId")
                checkout_url = hr_data.get("Data", {}).get("CheckoutUrl")
                payments[payment_id]["status"]     = "PENDING_CUSTOMER"
                payments[payment_id]["hubtel_ref"] = hubtel_ref
                if checkout_url:
                    payment_url = checkout_url
                logger.info(f"Hubtel MoMo prompt sent: ref={hubtel_ref} url={payment_url}")
            else:
                # Hubtel rejected — log and stay in mock mode for dev graceful fallback
                err = hr_data.get("Message") or hr_data.get("message") or hr.text[:200]
                logger.warning(f"Hubtel rejected: {hr.status_code} — {err}")
                log_alert("WARNING", f"Hubtel initiate failed for {payment_id}: {err}")

        except Exception as e:
            logger.error(f"Hubtel initiate error: {e}")
            log_alert("ERROR", f"Hubtel initiate exception: {e}")
            # Non-fatal — customer can still use mock_pay in dev / we return mock URL

    return {
        "payment_id":  payment_id,
        "payment_url": payment_url,
        "hubtel_ref":  hubtel_ref,
        "status":      payments[payment_id]["status"],
    }


@app.get("/payments/mock_pay/{payment_id}")
async def mock_pay(payment_id: str):
    """Simple page simulation for local testing: this endpoint simulates a successful Hubtel payment
    by returning instructions and a test notify link (`/payments/mock_notify/{payment_id}`) that will
    call the webhook endpoint to mark the payment as PAID.
    """
    if payment_id not in payments:
        raise HTTPException(status_code=404, detail="payment not found")

    notify_url = f"/payments/mock_notify/{payment_id}"
    return {
        "message": "Mock payment page",
        "payment_id": payment_id,
        "next": "Call the mock notify endpoint to simulate Hubtel callback",
        "mock_notify": notify_url,
    }


@app.post("/payments/mock_notify/{payment_id}")
async def mock_notify(payment_id: str, request: Request):
    """Simulate Hubtel's callback to our `/payments/callback` endpoint.
    This helper is only for local/dev testing.
    """
    if payment_id not in payments:
        raise HTTPException(status_code=404, detail="payment not found")

    # Mark the payment as PAID locally (best-effort for local/dev testing)
    payments[payment_id]["status"] = "PAID"

    # Build a fake callback payload (Hubtel sends its own shape; adapt as needed)
    callback_payload = {"payment_id": payment_id, "status": "PAID"}

    # Call our own callback endpoint to process the payment (best-effort)
    try:
        async with httpx.AsyncClient() as client:
            cb_port = os.environ.get("API_PORT", "8200")
            cb_url = f"http://localhost:{cb_port}/payments/callback"
            await client.post(cb_url, json=callback_payload, timeout=5.0)
    except Exception:
        # Swallow exceptions in dev mode; status has been set above
        pass

    return {"notified": True, "status": payments[payment_id]["status"]}


@app.post("/payments/callback")
async def callback(payload: dict):
    """Hubtel will POST payment results here. For MVP we accept a simple JSON with
    `payment_id` and `status`. Implement signature verification here when wiring real Hubtel.
    """
    payment_id = payload.get("payment_id")
    status = payload.get("status")
    if not payment_id or not status:
        raise HTTPException(status_code=400, detail="invalid payload")

    p = payments.get(payment_id)
    if not p:
        raise HTTPException(status_code=404, detail="payment not found")

    # Accept only PAID for now
    if status == "PAID":
        p["status"] = "ESCROW"
        # credit merchant (rider company) escrow balance
        merchant_amount = p.get("merchant_amount", 0)
        company_id = p.get("metadata", {}).get("company_id")
        if company_id:
            company_balances[company_id] = company_balances.get(company_id, 0) + merchant_amount
            transactions.append({
                "type": "credit",
                "company_id": company_id,
                "amount": merchant_amount,
                "payment_id": payment_id,
                "ts": int(time.time()),
            })
        # In a full flow, notify Order Service (create order) or update DB here.
        # Notify user that payment is received (order placed)
        try:
            phone = p.get("phone")
            if NOTIFICATION_SERVICE_URL and phone:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(f"{NOTIFICATION_SERVICE_URL}/notify/event", json={"phone": phone, "event": "order_placed", "order_id": payment_id})
        except Exception:
            pass

        # Create order in Order Service
        try:
            if ORDER_SERVICE_URL:
                payload = {
                    "payment_id": payment_id,
                    "amount": p.get("amount"),
                    "currency": p.get("currency","GHS"),
                    "phone": p.get("phone"),
                    "metadata": p.get("metadata", {}),
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(f"{ORDER_SERVICE_URL}/orders/create", json=payload)
        except Exception:
            pass

        return {"ok": True}

    p["status"] = status
    return {"ok": True}


# ==================== Webhook Verification ====================

@app.post("/payments/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming payment webhook from Hubtel with signature verification.
    
    Verifies HMAC-SHA256 signature before processing.
    Supports both new PostgreSQL-backed and legacy MVP flow.
    """
    
    # Get webhook secret from environment
    webhook_secret = os.environ.get("HUBTEL_WEBHOOK_SECRET")
    
    if not webhook_secret:
        # No signature secret configured — accept webhook but log warning
        # (acceptable for dev/sandbox; set HUBTEL_WEBHOOK_SECRET in production)
        logger.warning("HUBTEL_WEBHOOK_SECRET not configured — skipping signature check")
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="invalid JSON body")
        is_valid = True
    else:
        try:
            body, is_valid = await verify_hubtel_webhook(request, secret=webhook_secret)
        except HTTPException as e:
            # Log failed verification
            webhook_audit.log(
                provider="hubtel",
                event_type="payment",
                status="failed",
                error=str(e.detail)
            )
            logger.error(f"Webhook signature verification failed: {e.detail}")
            raise
    
    try:
        # ── Normalise Hubtel's real webhook shape ─────────────────────────────
        # Real Hubtel format (Receive Money callback):
        # { "ResponseCode": "0000", "Data": { "ClientReference": "uuid",
        #   "Status": "Success", "Amount": "5.00", "CustomerMsisdn": "233..." } }
        # Legacy/mock format: { "payment_id": "...", "status": "PAID" }
        if "Data" in body and isinstance(body["Data"], dict):
            data_block = body["Data"]
            body = {
                "payment_id":  data_block.get("ClientReference") or body.get("payment_id"),
                "status":      "PAID" if data_block.get("Status","").lower() in ("success","completed") else data_block.get("Status","FAILED").upper(),
                "reference":   data_block.get("TransactionId") or data_block.get("ClientReference"),
                "amount":      data_block.get("Amount"),
                "response_code": body.get("ResponseCode"),
            }

        # Extract payment details from webhook
        payment_id = body.get('payment_id')
        webhook_status = body.get('status', '').upper()
        reference = body.get('reference') or body.get('transaction_id')
        amount = body.get('amount')
        
        if not payment_id:
            webhook_audit.log(
                provider="hubtel",
                event_type="payment",
                status="failed",
                error="Missing payment_id in webhook"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing payment_id"
            )
        
        # Try PostgreSQL first, fall back to MVP store
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment and payment_id in payments:
            # Legacy MVP payment
            payment_data = payments[payment_id]
        elif not payment:
            webhook_audit.log(
                provider="hubtel",
                event_type="payment",
                status="failed",
                error=f"Payment {payment_id} not found"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Update payment status based on webhook status
        if webhook_status in ['COMPLETED', 'SUCCESS', 'PAID']:
            if payment:  # PostgreSQL
                payment.status = PaymentStatus.COMPLETED
                payment.hubtel_payment_id = reference or payment.hubtel_payment_id
                payment.completed_at = datetime.utcnow()
                db.commit()
            else:  # MVP
                payments[payment_id]['status'] = 'PAID'
                payments[payment_id]['reference'] = reference
            
            event_type = "payment.completed"
            
            # Notify notification service
            try:
                phone = payment.user.phone if payment else payment_data.get('phone')
                if os.environ.get("NOTIFICATION_SERVICE_URL") and phone:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        await client.post(
                            f"{os.environ.get('NOTIFICATION_SERVICE_URL')}/notify/event",
                            json={
                                "phone": phone,
                                "event": "payment_completed",
                                "payment_id": payment_id
                            },
                            timeout=5.0
                        )
            except Exception as e:
                logger.warning(f"Failed to send notification: {str(e)}")
        
        elif webhook_status in ['FAILED', 'DECLINED']:
            if payment:  # PostgreSQL
                payment.status = PaymentStatus.FAILED
                payment.hubtel_payment_id = reference or payment.hubtel_payment_id
                db.commit()
            else:  # MVP
                payments[payment_id]['status'] = 'FAILED'
            
            event_type = "payment.failed"
        
        else:
            event_type = f"payment.{webhook_status.lower()}"
        
        # Log successful webhook processing
        webhook_audit.log(
            provider="hubtel",
            event_type=event_type,
            status="success",
            details={
                "payment_id": payment_id,
                "reference": reference,
                "amount": amount,
                "webhook_status": webhook_status
            }
        )
        
        logger.info(f"Webhook processed: {payment_id} → {webhook_status}")
        
        return {
            "ok": True,
            "payment_id": payment_id,
            "status": webhook_status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        webhook_audit.log(
            provider="hubtel",
            event_type="payment",
            status="failed",
            error=str(e)
        )
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# ==================== Webhook Audit Log ====================

@app.get("/admin/webhook-logs")
async def get_webhook_logs(user = Depends(get_current_user)):
    """Get webhook audit trail (admin only)."""
    # Check user role (basic check, extend with RBAC as needed)
    user_data = user
    if user_data.get('role') != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only"
        )
    
    return {
        "logs": webhook_audit.get_log(limit=100),
        "total": len(webhook_audit.entries),
        "by_provider": {
            "hubtel": len(webhook_audit.get_by_provider("hubtel")),
            "stripe": len(webhook_audit.get_by_provider("stripe")),
            "paypal": len(webhook_audit.get_by_provider("paypal"))
        }
    }




@app.post("/payments/release/{payment_id}")
async def release_payment(payment_id: str):
    p = payments.get(payment_id)
    if not p:
        raise HTTPException(status_code=404, detail="payment not found")
    if p["status"] != "ESCROW":
        raise HTTPException(status_code=400, detail="payment not in escrow")
    p["status"] = "RELEASED"
    # In real system, credit the rider company account
    # For MVP, just mark as released
    return {"ok": True}


@app.post("/payouts/request")
async def request_payout(req: PayoutRequest):
    payout_id = str(uuid.uuid4())
    payouts[payout_id] = {
        "id": payout_id,
        "company_id": req.company_id,
        "amount": req.amount,
        "schedule": req.schedule,
        "status": "REQUESTED",
        "created_at": int(time.time()),
    }
    # In real system, schedule the payout
    return {"payout_id": payout_id, "status": "REQUESTED"}


@app.get("/payouts/{payout_id}")
async def get_payout(payout_id: str):
    p = payouts.get(payout_id)
    if not p:
        log_alert("error", f"Payout not found: {payout_id}")
        raise HTTPException(status_code=404, detail="payout not found")
    return p


@app.get("/companies/{company_id}/balance")
async def company_balance(company_id: str):
    return {"company_id": company_id, "balance": company_balances.get(company_id, 0)}


async def _payout_worker():
    """Background worker that processes scheduled payouts from `payouts`.
    Schedules: immediate, 3day, weekly
    """
    schedule_seconds = {"immediate": 0, "3day": 3 * 24 * 3600, "weekly": 7 * 24 * 3600}
    while True:
        now = int(time.time())
        for pid, po in list(payouts.items()):
            # Only process requested or retry-scheduled payouts
            if po.get("status") not in ("REQUESTED", "RETRY_SCHEDULED"):
                continue
            # support scheduled payout windows and retries
            sched = po.get("schedule") or "immediate"
            offset = schedule_seconds.get(sched, 0)
            next_run = po.get("next_run") or (po.get("created_at", 0) + offset)
            if next_run > now:
                continue
            # attempt to process
            cid = po.get("company_id")
            amt = int(po.get("amount", 0))
            bal = company_balances.get(cid, 0)
            if bal >= amt:
                # attempt Hubtel payout if configured
                sent = False
                hubtel_ref = None
                if HUBTEL_PAYOUT_URL and HUBTEL_PAYOUT_API_KEY:
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            # simple payout payload; adapt for Hubtel's API
                            pay_payload = {
                                "amount": amt,
                                "currency": "GHS",
                                "beneficiary": {"company_id": cid},
                                "metadata": {"payout_id": pid},
                            }
                            headers = {"Authorization": f"Bearer {HUBTEL_PAYOUT_API_KEY}"}
                            r = await client.post(HUBTEL_PAYOUT_URL, json=pay_payload, headers=headers)
                            if r.status_code in (200, 201):
                                jr = r.json()
                                # Hubtel may return an id/reference we can store
                                hubtel_ref = jr.get("reference") or jr.get("id")
                                sent = True
                    except Exception:
                        sent = False

                if sent:
                    # debit balance and mark sent; final confirmation may come via webhook
                    company_balances[cid] = bal - amt
                    po["status"] = "SENT"
                    po["processed_at"] = now
                    po["hubtel_ref"] = hubtel_ref
                    po["retries"] = po.get("retries", 0)
                    transactions.append({
                        "type": "debit",
                        "company_id": cid,
                        "amount": amt,
                        "payout_id": pid,
                        "ts": now,
                        "hubtel_ref": hubtel_ref,
                    })
                else:
                    # schedule retry with exponential backoff (do not debit)
                    po["retries"] = po.get("retries", 0) + 1
                    retry_count = po["retries"]
                    # backoff: 60s, 300s, 1800s, then mark failed after 5 tries
                    backoff = {1: 60, 2: 300, 3: 1800, 4: 3600, 5: 7200}.get(retry_count, 7200)
                    if retry_count >= 5:
                        po["status"] = "FAILED"
                        po["reason"] = "hubtel_error_or_not_configured"
                        po["processed_at"] = now
                        log_alert("error", f"Payout {pid} failed after retries (company={cid}, amt={amt})")
                    else:
                        po["status"] = "RETRY_SCHEDULED"
                        po["next_run"] = now + backoff
                        po["reason"] = "hubtel_error_scheduled_retry"
                        po["last_retry_at"] = now
                        log_alert("warning", f"Payout {pid} scheduled retry {retry_count} (company={cid}, amt={amt})")
            else:
                po["status"] = "FAILED"
                po["reason"] = "insufficient_balance"
                po["processed_at"] = now
                log_alert("error", f"Payout {pid} failed: insufficient balance (company={cid}, amt={amt})")
        await asyncio.sleep(30)
# --- Admin alerts endpoint ---
@app.get("/admin/alerts")
def get_admin_alerts():
    with ALERT_LOCK:
        return {"alerts": list(ALERT_LOG)[-20:][::-1]}  # last 20, newest first


@app.on_event("startup")
async def start_payout_worker():
    asyncio.create_task(_payout_worker())


@app.post("/payouts/webhook")
async def payouts_webhook(payload: dict, request: Request):
    """Endpoint for Hubtel (or other payout provider) to POST payout results.
    Expected payload (MVP): {"payout_id": "...", "status": "COMPLETED"|"FAILED", "hubtel_ref": "..."}
    """
    # verify signature if configured
    raw = await request.body()
    if HUBTEL_WEBHOOK_SECRET:
        sig_header = request.headers.get(HUBTEL_SIGNATURE_HEADER, "")
        if not sig_header:
            raise HTTPException(status_code=401, detail="missing signature header")
        # support header formats like 'sha256=...' or raw hex
        sig_val = sig_header.split('=', 1)[-1]
        computed = hmac.new(HUBTEL_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, sig_val):
            raise HTTPException(status_code=401, detail="invalid signature")

    # parse JSON body (use raw to ensure exact content)
    try:
        body = json.loads(raw.decode() if isinstance(raw, (bytes, bytearray)) else raw)
    except Exception:
        body = payload or {}

    # Hubtel may include several field shapes; try common ones
    payout_id = body.get("payout_id") or body.get("id") or (body.get("metadata") or {}).get("payout_id")
    status = (body.get("status") or body.get("state") or "").upper()
    hubtel_ref = body.get("hubtel_ref") or body.get("reference") or body.get("transaction_id") or body.get("id")
    if not payout_id or not status:
        raise HTTPException(status_code=400, detail="payout_id and status required")
    po = payouts.get(payout_id)
    if not po:
        raise HTTPException(status_code=404, detail="payout not found")

    now = int(time.time())
    # reconcile statuses
    if status.upper() in ("COMPLETED", "SUCCESS"):
        po["status"] = "COMPLETED"
        po["hubtel_ref"] = hubtel_ref
        po["processed_at"] = now
    else:
        # failed: try to refund ledger if we had debited earlier
        prev_status = po.get("status")
        po["status"] = "FAILED"
        po["hubtel_ref"] = hubtel_ref
        po["processed_at"] = now
        # if we previously debited balance on send, refund
        if prev_status == "SENT":
            cid = po.get("company_id")
            amt = int(po.get("amount", 0))
            company_balances[cid] = company_balances.get(cid, 0) + amt
            transactions.append({
                "type": "refund",
                "company_id": cid,
                "amount": amt,
                "payout_id": payout_id,
                "ts": now,
            })
    # record webhook event for audit
    transactions.append({
        "type": "webhook",
        "payout_id": payout_id,
        "status": status,
        "hubtel_ref": hubtel_ref,
        "raw": body,
        "ts": now,
    })

    return {"ok": True}


@app.get("/transactions")
async def list_transactions():
    return {"transactions": transactions}


@app.get("/admin/payouts")
async def admin_list_payouts(status: Optional[str] = None, company_id: Optional[str] = None, limit: int = 50, offset: int = 0, user=Depends(get_current_user)):
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")
    res = [p for p in payouts.values()]
    if status:
        res = [p for p in res if p.get("status") == status]
    if company_id:
        res = [p for p in res if p.get("company_id") == company_id]
    return {"payouts": res[offset:offset+limit]}


@app.post("/admin/payouts/{payout_id}/retry")
async def admin_retry_payout(payout_id: str, user=Depends(get_current_user)):
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")
    po = payouts.get(payout_id)
    if not po:
        raise HTTPException(status_code=404, detail="payout not found")
    # reset status to REQUESTED and clear scheduling
    po["status"] = "REQUESTED"
    po.pop("next_run", None)
    po["retries"] = 0
    po["reason"] = None
    po["processed_at"] = None
    return {"ok": True, "payout": po}


@app.post("/admin/payouts/{payout_id}/cancel")
async def admin_cancel_payout(payout_id: str, user=Depends(get_current_user)):
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")
    po = payouts.get(payout_id)
    if not po:
        raise HTTPException(status_code=404, detail="payout not found")
    prev = po.get("status")
    po["status"] = "CANCELLED"
    po["cancelled_at"] = int(time.time())
    # if we debited ledger earlier (SENT), refund
    if prev == "SENT":
        cid = po.get("company_id")
        amt = int(po.get("amount", 0))
        company_balances[cid] = company_balances.get(cid, 0) + amt
        transactions.append({"type": "refund", "company_id": cid, "amount": amt, "payout_id": payout_id, "ts": int(time.time())})
    return {"ok": True, "payout": po}


@app.post("/admin/payouts/{payout_id}/reconcile")
async def admin_reconcile(payout_id: str, payload: dict, user=Depends(get_current_user)):
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")
    # reuse webhook reconcile logic
    status = (payload.get("status") or "").upper()
    hubtel_ref = payload.get("hubtel_ref")
    po = payouts.get(payout_id)
    if not po:
        raise HTTPException(status_code=404, detail="payout not found")
    now = int(time.time())
    if status in ("COMPLETED", "SUCCESS"):
        po["status"] = "COMPLETED"
        po["hubtel_ref"] = hubtel_ref
        po["processed_at"] = now
    else:
        prev_status = po.get("status")
        po["status"] = "FAILED"
        po["hubtel_ref"] = hubtel_ref
        po["processed_at"] = now
        if prev_status == "SENT":
            cid = po.get("company_id")
            amt = int(po.get("amount", 0))
            company_balances[cid] = company_balances.get(cid, 0) + amt
            transactions.append({"type": "refund", "company_id": cid, "amount": amt, "payout_id": payout_id, "ts": now})
    transactions.append({"type": "reconcile", "payout_id": payout_id, "status": status, "hubtel_ref": hubtel_ref, "ts": now})
    return {"ok": True, "payout": po}


@app.get("/admin/reconciliation/export")
async def admin_export_reconciliation(user=Depends(get_current_user)):
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")
    # simple CSV export of payouts
    import io, csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["payout_id","company_id","amount","status","created_at","processed_at","hubtel_ref","retries"])
    for p in payouts.values():
        w.writerow([p.get("id"), p.get("company_id"), p.get("amount"), p.get("status"), p.get("created_at"), p.get("processed_at"), p.get("hubtel_ref"), p.get("retries", 0)])
    return {"csv": buf.getvalue()}


@app.get("/admin/webhooks/log")
async def admin_webhook_log(user=Depends(get_current_user)):
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")
    logs = [t for t in transactions if t.get("type") == "webhook"]
    return {"webhooks": logs}


@app.get("/payments/status/{payment_id}")
async def get_payment_status(payment_id: str):
    p = payments.get(payment_id)
    if not p:
        raise HTTPException(status_code=404, detail="payment not found")
    return p

# ==================== Refund Processing ====================

class RefundRequest(BaseModel):
    """Request to refund a payment."""
    payment_id: str
    refund_amount: float
    reason: str  # cancellation, duplicate, system_error
    order_id: Optional[str] = None

class RefundResponse(BaseModel):
    """Response for refund request."""
    payment_id: str
    refund_amount: float
    refund_status: str  # pending, processing, completed, failed
    refund_reference: Optional[str] = None
    error: Optional[str] = None

@app.post("/payments/refund", response_model=RefundResponse)
async def refund_payment(request: RefundRequest, db: Session = Depends(get_db)):
    """
    Process a refund for a completed payment.
    
    Supports:
    - Hubtel: Via refund API (primary)
    - Falls back to logging for unsupported providers
    """
    
    payment = db.query(Payment).filter(Payment.id == request.payment_id).first()
    if not payment:
        logger.warning(f"Refund requested for non-existent payment: {request.payment_id}")
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund payment with status {payment.status.value}"
        )
    
    if request.refund_amount <= 0 or request.refund_amount > payment.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refund amount"
        )
    
    try:
        refund_id = str(uuid.uuid4())
        
        # Determine provider from payment_method field
        provider = (payment.payment_method or "hubtel").lower()
        refund_reference = None
        refund_status = "pending"
        error = None
        
        if payment.hubtel_payment_id:
            try:
                # Call Hubtel refund API
                async with httpx.AsyncClient(timeout=10.0) as client:
                    refund_response = await client.post(
                        "https://api.hubtel.com/v1/pay/refund",
                        json={
                            "transactionId": payment.hubtel_payment_id,
                            "amount": request.refund_amount,
                            "reason": request.reason
                        },
                        auth=(HUBTEL_CLIENT_ID, HUBTEL_CLIENT_SECRET),
                        timeout=10.0
                    )
                    
                    if refund_response.status_code in [200, 201]:
                        refund_data = refund_response.json()
                        refund_reference = refund_data.get("refundId", refund_id)
                        refund_status = "completed"
                        logger.info(f"Hubtel refund processed: {refund_reference} ({request.refund_amount} GHS)")
                    else:
                        refund_status = "failed"
                        error = f"Hubtel error: {refund_response.status_code}"
                        logger.error(f"Hubtel refund failed: {error}")
            
            except Exception as e:
                refund_status = "failed"
                error = str(e)
                logger.error(f"Hubtel refund error: {e}")
        
        else:
            refund_status = "failed"
            error = "Missing Hubtel payment reference for refund"
            logger.warning(f"Cannot refund: provider={provider}, hubtel_payment_id={payment.hubtel_payment_id}")
        
        # Store refund record
        log_alert("info", f"Refund {refund_id}: {refund_status} ({request.refund_amount} GHS from {provider})")
        
        return RefundResponse(
            payment_id=request.payment_id,
            refund_amount=request.refund_amount,
            refund_status=refund_status,
            refund_reference=refund_reference,
            error=error
        )
    
    except Exception as e:
        logger.error(f"Refund processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund"
        )

# ==================== Get Refund Status ====================

@app.get("/payments/{payment_id}/refund-status")
async def get_refund_status(payment_id: str, db: Session = Depends(get_db)):
    """Get refund status for a payment."""
    
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check refund logs
    refund_logs = [t for t in transactions if t.get("type") == "refund" and t.get("payment_id") == payment_id]
    
    if not refund_logs:
        return {
            "payment_id": payment_id,
            "refund_status": "none",
            "refund_amount": 0,
            "message": "No refunds for this payment"
        }
    
    latest_refund = max(refund_logs, key=lambda x: x.get("ts", 0))
    
    return {
        "payment_id": payment_id,
        "refund_status": latest_refund.get("status", "unknown"),
        "refund_amount": latest_refund.get("amount", 0),
        "refund_reference": latest_refund.get("refund_id"),
        "processed_at": latest_refund.get("processed_at")
    }
