# Webhook Verification Implementation

## Overview

This document covers webhook signature verification for payment providers (Hubtel, Stripe, PayPal). Ensures incoming webhooks are authentic and haven't been tampered with.

---

## Architecture

### Verification Flow

```
1. Webhook Received
     ↓
2. Extract Signature from Headers
     ↓
3. Get Raw Request Body
     ↓
4. Compute Expected Signature (HMAC-SHA256)
     ↓
5. Compare Signatures (Constant-Time Comparison)
     ↓
6. Process If Valid / Reject If Invalid
     ↓
7. Log to Audit Trail
```

### Security Considerations

✅ **HMAC-SHA256** - Industry-standard cryptographic signature
✅ **Constant-Time Comparison** - Prevents timing attacks
✅ **Replay Attack Protection** - Timestamp validation (for Stripe)
✅ **Audit Trail** - All webhook events logged
✅ **Algorithm Agnostic** - Supports SHA1, SHA256, SHA512, MD5

---

## Implementation

### WebhookVerifier Class

Core verification logic:

```python
from shared.webhooks import WebhookVerifier

# Initialize verifier with provider secret
verifier = WebhookVerifier(
    secret="your_hubtel_webhook_secret",
    algorithm='sha256'
)

# Verify signature
is_valid = verifier.verify(
    payload=raw_body,
    signature=signature_header_value
)
```

### Provider-Specific Handlers

#### Hubtel Webhook Verification

```python
from shared.webhooks import verify_hubtel_webhook
from fastapi import HTTPException

@app.post("/payments/webhook/hubtel")
async def hubtel_webhook(request: Request):
    """Handle Hubtel payment webhook."""
    try:
        body, is_valid = await verify_hubtel_webhook(
            request,
            secret=os.environ.get("HUBTEL_WEBHOOK_SECRET")
        )
    except HTTPException as e:
        # Log and handle invalid signature
        webhook_audit.log(
            provider="hubtel",
            event_type="payment",
            status="failed",
            error=str(e.detail)
        )
        raise
    
    # Process verified payment
    payment_id = body.get('payment_id')
    status = body.get('status')
    
    webhook_audit.log(
        provider="hubtel",
        event_type=f"payment.{status.lower()}",
        status="success",
        details={"payment_id": payment_id}
    )
    
    # Update payment in database
    # ...
    
    return {"ok": True}
```

**Hubtel Signature Format:**
- Header: `X-Hubtel-Signature`
- Value: Hex-encoded SHA256 HMAC

**Example:**
```
X-Hubtel-Signature: 9f86d081884c7d6d9ffd60014fc7ee77e2e61d0d45c45c396e4ff5537a9eb5ef
```

#### Stripe Webhook Verification

```python
from shared.webhooks import verify_stripe_webhook

@app.post("/payments/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe payment webhook."""
    try:
        body, is_valid = await verify_stripe_webhook(
            request,
            secret=os.environ.get("STRIPE_WEBHOOK_SECRET")
        )
    except HTTPException as e:
        webhook_audit.log(
            provider="stripe",
            event_type="event",
            status="failed",
            error=str(e.detail)
        )
        raise
    
    event_type = body.get('type')  # e.g., "charge.succeeded"
    data = body.get('data', {}).get('object', {})
    
    webhook_audit.log(
        provider="stripe",
        event_type=event_type,
        status="success",
        details={"charge_id": data.get('id')}
    )
    
    # Process based on event type
    if event_type == 'charge.succeeded':
        # Mark payment as completed
        pass
    elif event_type == 'charge.failed':
        # Mark payment as failed
        pass
    
    return {"ok": True}
```

**Stripe Signature Format:**
- Header: `Stripe-Signature`
- Value: `t=<timestamp>,v1=<signature>`
- Timestamp validation: 5-minute window

**Example:**
```
Stripe-Signature: t=1614556800,v1=9f86d081884c7d6d9ffd60014fc7ee77e2e61d0d45c45c396e4ff5537a9eb5ef
```

#### PayPal Webhook Verification

```python
from shared.webhooks import verify_paypal_webhook

@app.post("/payments/webhook/paypal")
async def paypal_webhook(request: Request):
    """Handle PayPal webhook."""
    try:
        body, is_valid = await verify_paypal_webhook(
            request,
            client_id=os.environ.get("PAYPAL_CLIENT_ID"),
            client_secret=os.environ.get("PAYPAL_CLIENT_SECRET")
        )
    except HTTPException as e:
        webhook_audit.log(
            provider="paypal",
            event_type="event",
            status="failed",
            error=str(e.detail)
        )
        raise
    
    event_type = body.get('event_type')
    resource = body.get('resource', {})
    
    webhook_audit.log(
        provider="paypal",
        event_type=event_type,
        status="success",
        details={"resource_id": resource.get('id')}
    )
    
    # Process event
    return {"ok": True}
```

**PayPal Signature Headers:**
```
Paypal-Transmission-Id: <transmission_id>
Paypal-Transmission-Time: <timestamp>
Paypal-Cert-Url: <certificate_url>
Paypal-Auth-Algo: SHA256withRSA
Paypal-Webhook-Signature: <signature>
Paypal-Webhook-Id: <webhook_id>
```

---

## Integration with Payment Service

### Updated Webhook Endpoint

```python
# In /services/payment_service/main.py

from shared.webhooks import verify_hubtel_webhook, webhook_audit
from fastapi import Request, HTTPException

@app.post("/payments/webhook")
async def payment_webhook(request: Request):
    """Handle incoming payment webhook (Hubtel)."""
    
    try:
        # Verify signature
        body, is_valid = await verify_hubtel_webhook(
            request,
            secret=os.environ.get("HUBTEL_WEBHOOK_SECRET")
        )
    except HTTPException as e:
        # Log failed verification
        webhook_audit.log(
            provider="hubtel",
            event_type="payment",
            status="failed",
            error=str(e.detail)
        )
        raise
    
    try:
        # Extract payment details
        payment_id = body.get('payment_id')
        status = body.get('status', '').upper()
        reference = body.get('reference')
        amount = body.get('amount')
        
        # Get payment from database
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            webhook_audit.log(
                provider="hubtel",
                event_type="payment",
                status="failed",
                error=f"Payment {payment_id} not found"
            )
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Update payment status
        if status in ['COMPLETED', 'SUCCESS']:
            payment.status = PaymentStatus.COMPLETED
            payment.reference = reference
            payment.completed_at = datetime.utcnow()
            
            # Trigger order creation if configured
            if os.environ.get("AUTO_CREATE_ORDER"):
                # Call order service to create order
                pass
        
        elif status in ['FAILED', 'DECLINED']:
            payment.status = PaymentStatus.FAILED
            payment.reference = reference
            payment.failed_at = datetime.utcnow()
        
        db.commit()
        
        # Log successful processing
        webhook_audit.log(
            provider="hubtel",
            event_type=f"payment.{status.lower()}",
            status="success",
            details={
                "payment_id": payment_id,
                "reference": reference,
                "amount": amount
            }
        )
        
        return {"ok": True, "payment_id": payment_id, "status": status}
    
    except Exception as e:
        db.rollback()
        webhook_audit.log(
            provider="hubtel",
            event_type="payment",
            status="failed",
            error=str(e)
        )
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
```

---

## API Endpoint Specifications

### POST /payments/webhook

Receives and verifies payment completion webhook from Hubtel.

**Headers Required:**
```
X-Hubtel-Signature: <hmac_signature>
Content-Type: application/json
```

**Request Body:**
```json
{
    "payment_id": "pay_123abc",
    "status": "COMPLETED",
    "reference": "HUB-REF-123",
    "amount": 2500,
    "currency": "GHS",
    "timestamp": "2026-01-31T10:30:00Z"
}
```

**Response 200:**
```json
{
    "ok": true,
    "payment_id": "pay_123abc",
    "status": "COMPLETED"
}
```

**Response 401 (Invalid Signature):**
```json
{
    "detail": "Invalid signature"
}
```

**Response 404 (Payment Not Found):**
```json
{
    "detail": "Payment not found"
}
```

---

## Error Handling

### Signature Verification Failures

```python
# Missing header
HTTP 401
{
    "detail": "Missing signature header"
}

# Invalid signature
HTTP 401
{
    "detail": "Invalid signature"
}

# Invalid JSON
HTTP 400
{
    "detail": "Invalid JSON payload"
}

# Timestamp too old (Stripe)
HTTP 401
{
    "detail": "Request timestamp outside acceptable window"
}
```

---

## Testing

### Unit Tests

```python
from shared.webhooks import WebhookVerifier
import hmac
import hashlib

def test_webhook_signature_verification():
    """Test HMAC signature verification."""
    secret = "test_secret"
    payload = b'{"payment_id": "123", "status": "COMPLETED"}'
    
    # Compute signature
    verifier = WebhookVerifier(secret, algorithm='sha256')
    signature = verifier.compute_signature(payload)
    
    # Verify correct signature
    assert verifier.verify(payload, signature) == True
    
    # Verify incorrect signature
    assert verifier.verify(payload, "wrong_signature") == False

def test_hubtel_webhook_with_prefix():
    """Test Hubtel signature with sha256= prefix."""
    secret = "test_secret"
    payload = b'{"payment_id": "123"}'
    
    verifier = WebhookVerifier(secret)
    signature = verifier.compute_signature(payload)
    
    # Should work with and without prefix
    assert verifier.verify(payload, signature) == True
    assert verifier.verify(payload, f"sha256={signature}") == True
```

### Integration Test

```bash
# Test Hubtel webhook locally

# Step 1: Compute signature
SECRET="your_hubtel_secret"
PAYLOAD='{"payment_id": "pay_123", "status": "COMPLETED"}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex | sed 's/.*= //')

# Step 2: Send webhook
curl -X POST http://localhost:8200/payments/webhook \
  -H "X-Hubtel-Signature: $SIGNATURE" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"

# Expected response:
# {"ok": true, "payment_id": "pay_123", "status": "COMPLETED"}
```

---

## Audit Trail

### Accessing Webhook Logs

```python
from shared.webhooks import webhook_audit

# Get last 100 webhook events
logs = webhook_audit.get_log(limit=100)

# Get events for specific provider
hubtel_logs = webhook_audit.get_by_provider("hubtel", limit=50)

# Each log entry contains:
# {
#     "timestamp": "2026-01-31T10:30:00",
#     "provider": "hubtel",
#     "event_type": "payment.completed",
#     "status": "success",
#     "details": {"payment_id": "pay_123", "amount": 2500},
#     "error": null
# }
```

### Admin Endpoint

```python
@app.get("/admin/webhook-logs")
async def get_webhook_logs(user=Depends(get_current_user)):
    """Get webhook audit trail (admin only)."""
    if user['role'] != 'superadmin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    return {
        "logs": webhook_audit.get_log(limit=100),
        "total": len(webhook_audit.entries)
    }
```

---

## Deployment Checklist

- [x] WebhookVerifier class implemented
- [x] Provider-specific handlers (Hubtel, Stripe, PayPal)
- [x] Signature verification with constant-time comparison
- [x] Audit logging for all webhook events
- [x] Error handling with proper HTTP status codes
- [x] Timestamp validation (replay attack prevention)
- [ ] Integration with payment service
- [ ] Environment variables configured
- [ ] Webhook URLs registered with providers
- [ ] Tests written and passing
- [ ] Production secrets securely stored

---

## Environment Variables

```bash
# Hubtel
HUBTEL_WEBHOOK_SECRET=hubtel_signing_secret_from_dashboard
HUBTEL_SIGNATURE_HEADER=X-Hubtel-Signature

# Stripe
STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx

# PayPal
PAYPAL_WEBHOOK_SECRET=paypal_signing_secret
PAYPAL_CLIENT_ID=client_id
PAYPAL_CLIENT_SECRET=client_secret
```

---

## Security Best Practices

1. **Never log secrets** - Never log webhook secrets or payment details
2. **Constant-time comparison** - Always use `hmac.compare_digest()` to prevent timing attacks
3. **Validate timestamps** - Reject webhooks outside acceptable time window (5 minutes)
4. **Validate content-type** - Ensure webhook is JSON before parsing
5. **Rate limit webhooks** - Prevent webhook flooding
6. **Retry logic** - Return 200 quickly, process asynchronously
7. **Idempotency** - Handle duplicate webhooks (same payment processed twice)
8. **IP whitelisting** - Optionally verify webhook source IP

---

## Future Enhancements

1. **Database-backed Audit Log** - Store in PostgreSQL instead of memory
2. **Webhook Replay** - Admin UI to manually replay webhooks for testing
3. **Webhook Filtering** - Subscribe to specific event types only
4. **Exponential Backoff** - Auto-retry failed payment processing
5. **Webhook Signing** - Sign our own webhooks to merchants
6. **Multi-Provider Support** - Easy switching between payment providers
7. **Webhook Metrics** - Prometheus metrics for webhook latency/success rate
8. **PII Masking** - Mask sensitive data in logs
