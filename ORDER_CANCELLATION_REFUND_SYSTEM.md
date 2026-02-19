# Order Cancellation & Refund System (Task 9)

## Overview

The Order Cancellation & Refund System enables merchants to cancel orders and automatically process refunds with payment providers. The system handles penalty calculations, refund retries, and comprehensive notification workflows.

**Features:**
- ✅ Order cancellation with reason tracking
- ✅ Automatic refund processing (Hubtel, Paystack)
- ✅ Penalty calculation (10% if picked up, 25% if in transit)
- ✅ Refund status tracking (pending, processing, completed, failed)
- ✅ Refund retry mechanism (admin only)
- ✅ Notification workflow (merchant, rider, customer)
- ✅ Cancellation audit trail
- ✅ Refund dispute handling

---

## Architecture

### Service Integration

```
Merchant cancels order
    ↓
Order Service validates cancellation
    ├─ Check status (can cancel at PENDING, ASSIGNED, PICKED_UP, IN_TRANSIT)
    ├─ Calculate refund amount with penalties
    └─ Update order.status = CANCELLED
    ↓
Payment Service processes refund
    ├─ Hubtel: Call refund API with transaction ID
    ├─ Paystack: Call refund API with transaction reference
    └─ Update refund_status
    ↓
Notification Service notifies stakeholders
    ├─ Email to merchant (cancellation confirmation)
    ├─ SMS to rider (delivery cancelled)
    └─ SMS/Email to customer (refund initiated)
```

### Database Models

**Order Model Additions:**
```python
cancelled_at: DateTime              # When order was cancelled
cancellation_reason: String         # customer_request, merchant_cancel, system_failure, rider_unavailable
refund_amount: Float               # Amount to be refunded (after penalties)
refund_status: String              # none, pending, processing, completed, failed
```

---

## API Endpoints

### 1. Cancel Order

**POST** `/orders/{order_id}/cancel`

Cancel an order and initiate refund.

**Request:**
```json
{
  "reason": "customer_request",
  "notes": "Customer changed their mind"
}
```

**Query Parameters:**
- `reason` (optional, default='customer_request'): Cancellation reason
  - `customer_request`: Customer cancelled
  - `merchant_cancel`: Merchant cancelled
  - `system_failure`: System error
  - `rider_unavailable`: Rider not available

**Response (200):**
```json
{
  "order_id": "ORD-12345",
  "previous_status": "ASSIGNED",
  "new_status": "CANCELLED",
  "cancellation_reason": "customer_request",
  "refund_amount_ghs": 45.00,
  "refund_status": "processing",
  "cancelled_at": "2026-01-31T10:30:00Z"
}
```

**Validation:**
- Order must exist
- Only order creator or admin can cancel
- Order status must allow cancellation (not DELIVERED)
- Refund amount calculated based on status

**Effects:**
- Order status → CANCELLED
- Refund initiated (pending → processing)
- Merchant notified via email
- Rider notified via SMS (if assigned)

**Errors:**
- `404 Not Found`: Order doesn't exist
- `403 Forbidden`: Not authorized to cancel
- `400 Bad Request`: Order cannot be cancelled (already delivered)

---

### 2. Refund Penalty Calculation

**Refund Rules:**
```
Status at Cancellation  | Refund Amount
─────────────────────────────────────
PENDING                 | 100% refund
ASSIGNED                | 100% refund (rider hasn't picked up yet)
PICKED_UP               | 90% refund (10% penalty for rider time)
IN_TRANSIT               | 75% refund (25% penalty for rider journey)
DELIVERED               | Cannot cancel (0% refund)
```

**Examples:**
```
Example 1: Cancel at PENDING
  Original: 50 GHS
  Penalty: 0%
  Refund: 50 GHS

Example 2: Cancel at PICKED_UP
  Original: 50 GHS
  Penalty: 10%
  Refund: 45 GHS

Example 3: Cancel at IN_TRANSIT
  Original: 50 GHS
  Penalty: 25%
  Refund: 37.50 GHS
```

---

### 3. Get Refund Status

**GET** `/orders/{order_id}/refund-status`

Get refund status for a cancelled order.

**Response (200):**
```json
{
  "order_id": "ORD-12345",
  "refund_amount": 45.00,
  "refund_status": "completed",
  "cancellation_reason": "customer_request",
  "cancelled_at": "2026-01-31T10:30:00Z"
}
```

**Refund Status Values:**
- `none`: Not cancelled
- `pending`: Refund initiated, awaiting processing
- `processing`: Refund in progress with payment provider
- `completed`: Refund successfully processed
- `failed`: Refund failed, needs retry

**Errors:**
- `404 Not Found`: Order doesn't exist
- `403 Forbidden`: Not authorized
- `400 Bad Request`: Order not cancelled

---

### 4. Refund Payment (Payment Service)

**POST** `/payments/refund`

Process refund for a completed payment.

**Request:**
```json
{
  "payment_id": "PAY-001",
  "refund_amount": 45.00,
  "reason": "cancellation",
  "order_id": "ORD-12345"
}
```

**Response (200):**
```json
{
  "payment_id": "PAY-001",
  "refund_amount": 45.00,
  "refund_status": "completed",
  "refund_reference": "HUBTEL-REF-123",
  "error": null
}
```

**Provider Integration:**

**Hubtel:**
```
POST https://api.hubtel.com/v1/pay/refund
  - transactionId: Payment's Hubtel reference
  - amount: Refund amount in GHS
  - reason: Cancellation reason

Response:
  - refundId: Unique refund identifier
  - status: SUCCESS/FAILURE
```

**Paystack:**
```
POST https://api.paystack.co/refund
  - transaction: Transaction ID or reference
  - amount: Refund amount in kobo (amount * 100)

Response:
  - reference: Refund reference
  - status: success/pending/failed
  - data: Refund details
```

---

### 5. Get Refund Status (Payment Service)

**GET** `/payments/{payment_id}/refund-status`

Get refund status from payment provider.

**Response (200):**
```json
{
  "payment_id": "PAY-001",
  "refund_status": "completed",
  "refund_amount": 45.00,
  "refund_reference": "HUBTEL-REF-123",
  "processed_at": "2026-01-31T10:45:00Z"
}
```

---

### 6. Admin: Retry Refund

**POST** `/admin/refunds/{order_id}/retry`

Retry a failed refund (admin only).

**Response (200):**
```json
{
  "ok": true,
  "message": "Refund retry initiated"
}
```

**Conditions:**
- Order must be cancelled
- Refund status must be "failed"
- Payment must exist

**Process:**
1. Mark refund as pending
2. Call payment service refund API again
3. Log retry attempt
4. Notify merchant of retry

---

## Data Models

### Order Cancellation Fields

```python
# Cancellation tracking
cancelled_at: DateTime              # When cancelled
cancellation_reason: String         # Why cancelled
refund_amount: Float               # Amount to refund (after penalties)
refund_status: String              # Status of refund processing
```

### Refund Workflow States

```
Initial State: order.status ≠ CANCELLED
    ↓
Merchant clicks Cancel
    ├─ Check if cancellable
    ├─ Calculate refund amount
    ├─ Set status → CANCELLED
    └─ refund_status → "pending"
    ↓
Payment Service processes
    ├─ Call provider API
    ├─ Provider returns refund_id
    └─ refund_status → "processing"
    ↓
Webhook from provider (if supported)
    ├─ Confirm refund success
    └─ refund_status → "completed"
    ↓
OR refund_status → "failed"
    └─ Admin can retry from here
```

---

## Usage Examples

### Cancel an Order

```bash
# Merchant cancels their own order
curl -X POST http://localhost:8400/orders/ORD-12345/cancel \
  -H "Authorization: Bearer MERCHANT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "customer_request",
    "notes": "Customer requested cancellation"
  }'

Response:
{
  "order_id": "ORD-12345",
  "previous_status": "ASSIGNED",
  "new_status": "CANCELLED",
  "cancellation_reason": "customer_request",
  "refund_amount_ghs": 45.00,
  "refund_status": "processing",
  "cancelled_at": "2026-01-31T10:30:00Z"
}
```

### Check Refund Status

```bash
# Check if refund completed
curl http://localhost:8400/orders/ORD-12345/refund-status \
  -H "Authorization: Bearer MERCHANT_TOKEN"

Response:
{
  "order_id": "ORD-12345",
  "refund_amount": 45.00,
  "refund_status": "completed",
  "cancellation_reason": "customer_request",
  "cancelled_at": "2026-01-31T10:30:00Z"
}
```

### Admin Retry Failed Refund

```bash
# Admin retries a failed refund
curl -X POST http://localhost:8400/admin/refunds/ORD-12345/retry \
  -H "Authorization: Bearer ADMIN_TOKEN"

Response:
{
  "ok": true,
  "message": "Refund retry initiated"
}
```

---

## Notification Workflow

### Email to Merchant

**Subject:** Order Cancelled - Refund Processing

```
Dear [Merchant],

Your order ORD-12345 has been cancelled.

Cancellation Details:
- Order ID: ORD-12345
- Cancellation Reason: Customer Request
- Original Amount: 50.00 GHS
- Refund Amount: 45.00 GHS (10% penalty)
- Status: Refund Processing

Your refund will be completed within 3-5 business days.

Best regards,
Delivery Platform
```

### SMS to Rider

```
Order ORD-12345 has been cancelled by the merchant.
No longer needed for delivery.
```

### SMS to Customer

```
Your order ORD-12345 has been cancelled.
Refund of 45.00 GHS is being processed.
Expected within 3-5 business days.
```

---

## Error Handling

### Cancellation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Order not found | Invalid order_id | Check order ID |
| Not authorized | Not order creator | Use correct account |
| Cannot cancel | Already delivered | Only pending/in-progress orders |
| Invalid reason | Unknown reason | Use valid reason value |

### Refund Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Payment not found | Missing payment record | Check payment_id |
| Invalid status | Payment not completed | Only complete payments refundable |
| Invalid amount | Negative or > original | Refund must be 0 < x ≤ original |
| Provider error | API down/error | Retry with /admin/refunds/retry |
| No provider ref | Missing transaction ID | Check payment provider details |

---

## Security Considerations

### Authorization
- Only merchant/admin can cancel orders
- Only order creator can check refund status
- Admins can retry failed refunds

### Validation
- Order must exist before cancellation
- Amount must be valid (positive, ≤ original)
- Status must allow cancellation
- Reason must be from allowed list

### Audit Trail
- All cancellations logged with timestamp
- Refund attempts tracked
- Provider responses stored
- Admin retry actions logged

---

## Testing Scenarios

### Happy Path

```
1. ✅ Create order (50 GHS)
2. ✅ Assign rider (still 100% refund)
3. ✅ Cancel order at ASSIGNED status
4. ✅ Refund 50 GHS to customer
5. ✅ Verify status = "completed"
6. ✅ Notify all parties
```

### Penalty Scenarios

```
1. ✅ Cancel at PENDING: 100% refund
2. ✅ Cancel at ASSIGNED: 100% refund
3. ✅ Cancel at PICKED_UP: 90% refund (10% penalty)
4. ✅ Cancel at IN_TRANSIT: 75% refund (25% penalty)
5. ✅ Cannot cancel at DELIVERED: Error 400
```

### Refund Failures

```
1. ✅ Provider API timeout: refund_status = "failed"
2. ✅ Invalid payment reference: refund_status = "failed"
3. ✅ Admin retries: refund_status = "pending" → "processing"
4. ✅ Provider rejects: refund_status = "failed" (permanent)
```

---

## Integration Points

### With Order Service
- Cancellation endpoint in order_service
- Validates order status and permissions
- Calculates refund with penalties
- Updates order record

### With Payment Service
- Processes refund with provider
- Returns refund reference
- Tracks refund status
- Supports retry mechanism

### With Notification Service
- Sends cancellation confirmation to merchant
- Notifies rider of cancellation
- Informs customer of refund
- Tracks notification delivery

### With Tracking Service
- Cancels active tracking session
- Updates tracking status
- Notifies subscribers (if connected via WebSocket)

---

## Deployment

### Environment Variables

```bash
# Payment Provider Credentials
HUBTEL_CLIENT_ID=your-id
HUBTEL_CLIENT_SECRET=your-secret
PAYSTACK_SECRET_KEY=sk_live_...
PAYSTACK_PUBLIC_KEY=pk_live_...

# Service URLs
ORDER_SERVICE_URL=http://localhost:8400
PAYMENT_SERVICE_URL=http://localhost:8300
NOTIFICATION_SERVICE_URL=http://localhost:8600
TRACKING_SERVICE_URL=http://localhost:8500
```

### Database Migration

```sql
-- Add columns to orders table
ALTER TABLE orders ADD COLUMN cancelled_at TIMESTAMP NULL;
ALTER TABLE orders ADD COLUMN cancellation_reason VARCHAR(255) NULL;
ALTER TABLE orders ADD COLUMN refund_amount FLOAT NULL;
ALTER TABLE orders ADD COLUMN refund_status VARCHAR(50) DEFAULT 'none';

-- Create index for performance
CREATE INDEX idx_cancelled_orders ON orders(cancelled_at DESC);
CREATE INDEX idx_refund_status ON orders(refund_status);
```

---

## Monitoring

### Key Metrics

```
- Cancellation rate (% of orders cancelled)
- Refund success rate (% of refunds completed)
- Average refund processing time
- Failed refund count (needs admin attention)
- Penalty amount collected
```

### Logs to Monitor

```
INFO: Order cancelled: ORD-12345 (reason=customer_request, refund=50.00)
ERROR: Hubtel refund failed: transaction not found
WARNING: Refund retry attempted for ORD-12345
INFO: Refund completed: ORD-12345 (ref=HUBTEL-123)
```

---

## Summary

The Order Cancellation & Refund System provides:

✅ **Automatic Refunds:** Hubtel, Paystack integration  
✅ **Penalty Calculation:** 10% if picked up, 25% if in transit  
✅ **Refund Tracking:** Pending → Processing → Completed/Failed  
✅ **Retry Mechanism:** Admin can retry failed refunds  
✅ **Notifications:** Merchant, rider, customer alerts  
✅ **Audit Trail:** Complete cancellation and refund history  
✅ **Error Handling:** Graceful handling of provider failures  

**Key Features:**
- 3 cancellation endpoints (cancel, status, retry)
- 2 payment refund endpoints (refund, status)
- Penalty-based refund calculation
- Multi-provider support (Hubtel, Paystack)
- Comprehensive notification workflow
- Admin management capabilities

**Next Task:** Mobile Responsiveness (Task 10)
