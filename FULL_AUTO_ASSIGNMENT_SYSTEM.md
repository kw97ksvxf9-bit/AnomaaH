# Full Auto-Assignment System (No Manual Order Pool)

**Effective Date:** January 31, 2026  
**Status:** ✅ ACTIVE  

---

## Overview

The platform now operates on a **fully automatic rider assignment system**. When an order is created and payment is completed, it is immediately assigned to the optimal rider using intelligent scoring. The manual **Order Pool** has been removed.

**Key Benefits:**
- ✅ Faster order fulfillment (instant assignment)
- ✅ Optimal rider matching (5-factor scoring)
- ✅ Reduced manual intervention
- ✅ Better customer experience
- ✅ Simplified operations

---

## Order Lifecycle (Auto-Assignment)

### 1. **Booking Stage**
```
Customer books a ride via mobile app
↓
System calculates:
  - Distance (km)
  - ETA (minutes)
  - Price (GHS)
  - Pickup/Dropoff coordinates
```

### 2. **Payment Stage**
```
Customer pays via Hubtel or Paystack
↓
Payment Service validates transaction
↓
Order is created with status = PENDING
```

### 3. **Auto-Assignment (Immediate)**
```
Order Service receives order creation request
↓
Creates order record in database
↓
Immediately calls Assignment Service with:
  - order_id
  - order_lat / order_lng
  - strategy = "hybrid" (default)
  - company_id (merchant/company)
↓
Assignment Service calculates scores for all available riders:
  ├─ Active riders only (status = online)
  ├─ With min rating (3.5★)
  ├─ With < 3 active orders
  └─ Score formula:
      Final Score = (
        0.40 × Proximity Score    +
        0.30 × Rating Score       +
        0.20 × Load Balance Score +
        0.10 × Speed Score
      )
↓
Best rider selected and assigned
↓
Order status → ASSIGNED
↓
Tracking started automatically
↓
Notifications sent to merchant & rider
```

### 4. **Order Fulfillment**
```
Rider receives notification & sees order
↓
Rider accepts and starts navigation
↓
Pickup → In-Transit → Delivery → Completed
```

---

## API Flow

### Order Creation → Auto-Assignment Chain

**Step 1: Order Service (POST /orders/create)**
```python
# Client Request
POST /orders/create
{
  "payment_id": "pay_123",
  "pickup_address": "Accra Downtown",
  "pickup_lat": 5.6,
  "pickup_lng": -0.18,
  "dropoff_address": "Tema",
  "dropoff_lat": 5.64,
  "dropoff_lng": -0.24,
  "distance_km": 30.5,
  "eta_min": 45,
  "price_ghs": 5050.00
}

# Response (Order Created)
{
  "id": "order_xyz",
  "status": "PENDING",  ← Initial status
  "pickup_address": "Accra Downtown",
  "dropoff_address": "Tema",
  ...
}
```

**Step 2: Auto-Assignment (Internal - POST /orders/auto-assign)**
```python
# Order Service calls Assignment Service
POST http://localhost:8100/orders/auto-assign
{
  "order_id": "order_xyz",
  "order_lat": 5.6,
  "order_lng": -0.18,
  "company_id": "merchant_123",
  "strategy": "hybrid"
}

# Response (Rider Assigned)
{
  "success": true,
  "message": "Order assigned successfully",
  "rider_id": "rider_456",
  "rider_name": "John Doe",
  "distance_km": 2.3,
  "score": 0.92,
  "score_breakdown": {
    "proximity": 0.95,
    "rating": 0.88,
    "load_balance": 0.90,
    "speed": 0.85
  }
}

# Order status automatically updated to ASSIGNED
```

**Step 3: Tracking Started (Internal)**
```python
# Assignment Service calls Tracking Service
POST http://localhost:8300/tracking/start
{
  "order_id": "order_xyz",
  "rider_id": "rider_456"
}

# Real-time tracking begins
```

**Step 4: Notifications Sent**
```python
# Notification Service sends alerts
POST /notify/event
{
  "phone": "merchant_phone",
  "event": "order_placed",
  "order_id": "order_xyz"
}

# Rider receives order notification on app
```

---

## Scoring Factors (5-Factor HYBRID Strategy)

### 1. **Proximity Score** (40% weight)
**Formula:** Exponential decay based on distance
```
score = e^(-k × distance)
where k = ln(10) / 50 km (max distance)

Examples:
- 0 km away = 1.0 (perfect)
- 2 km away = 0.87
- 5 km away = 0.77
- 10 km away = 0.61
- 20 km away = 0.37
- 50+ km away = 0.0 (too far, excluded)
```

### 2. **Rating Score** (30% weight)
**Formula:** Normalized from 5-star system
```
score = average_rating / 5.0

Examples:
- 5.0 stars = 1.0 (perfect)
- 4.5 stars = 0.9
- 4.0 stars = 0.8
- 3.5 stars = 0.7
- < 3.5 stars = excluded (minimum threshold)
```

### 3. **Load Balance Score** (20% weight)
**Formula:** Penalize busy riders
```
score = 1.0 - (active_orders / max_orders)
Default max_orders = 3

Examples:
- 0 active orders = 1.0 (available)
- 1 active order = 0.67
- 2 active orders = 0.33
- 3 active orders = 0.0 (at capacity)
```

### 4. **Speed Score** (10% weight)
**Formula:** Normalized delivery time
```
target_delivery_time = 60 minutes

score = max(0, 1.0 - (avg_delivery_time / target_delivery_time))

Examples:
- 30 min avg = 1.0 (excellent)
- 60 min avg = 1.0 (on target)
- 90 min avg = 0.5 (slow)
- 120+ min avg = 0.0 (too slow)
```

### 5. **Final Score Calculation**
```python
final_score = (
    0.40 × proximity_score +
    0.30 × rating_score +
    0.20 × load_balance_score +
    0.10 × speed_score
)

Range: 0.0 (worst) to 1.0 (best)
Tie-breaker: Highest proximity if scores are equal
```

---

## Rider Eligibility Criteria

An order is only assigned to riders who meet ALL criteria:

| Criterion | Requirement | Reason |
|-----------|-------------|--------|
| **Account Status** | Active | Must have valid account |
| **Online Status** | Online | Must be actively working |
| **Minimum Rating** | ≥ 3.5 stars | Quality assurance |
| **Active Orders** | < 3 orders | Workload capacity limit |
| **Distance** | ≤ 50 km | Service radius limit |
| **Account Verified** | Yes | Safety & compliance |

**If no eligible riders found:**
```
Status: Assignment Failed
Message: "No available riders in your area"
Order remains: PENDING
Retry: Automatic retry every 30 seconds (up to 5 times)
Fallback: Manual assignment available via admin
```

---

## Assignment Strategies (Optional Override)

While HYBRID is the default, the system supports alternative strategies:

### 1. **HYBRID** (Default - Recommended)
- Balanced scoring of all 5 factors
- Best overall optimal matching
- Use case: General orders

### 2. **PROXIMITY**
- 100% weight on distance
- Closest rider wins
- Use case: Time-sensitive urban orders

### 3. **BALANCED_LOAD**
- 100% weight on load balance
- Even distribution across riders
- Use case: Peak hours, fair allocation

### 4. **HIGHEST_RATING**
- 100% weight on rating
- Best-rated riders first
- Use case: VIP/premium orders

### 5. **FASTEST_DELIVERY**
- 100% weight on speed history
- Fastest riders first
- Use case: Time-critical deliveries

---

## Admin Dashboard Changes

### What Changed?
| Feature | Before | After |
|---------|--------|-------|
| **Order Pool** | Manual assignment interface | ✅ Removed |
| **Manual Assign Button** | Available | ✅ Removed |
| **Rider Selection Dropdown** | Visible in pool | ✅ Removed |
| **Auto-Assignment Display** | Not shown | ✅ Added (status indicator) |

### New Dashboard Layout
```
┌─ Company Dashboard ─────────────────┐
│                                      │
│ [Auto-Assignment Status]             │
│ ✓ Active - Orders auto-assigned      │
│                                      │
│ [Stats Cards]                        │
│ - Total Orders                       │
│ - Active Orders                      │
│ - Completed Orders                   │
│ - Riders                             │
│                                      │
│ [Rider Leaderboard]                  │
│ - Performance metrics                │
│ - Online status                      │
│ - Earnings & Payouts                 │
│ - Document management                │
│                                      │
│ [Orders List]                        │
│ - All orders (PENDING → DELIVERED)   │
│ - Real-time status                   │
│ - Tracking links                     │
│                                      │
└──────────────────────────────────────┘
```

---

## Error Handling & Fallbacks

### Scenario 1: Auto-Assignment Fails
```
When: No eligible riders found
Action: Order stays PENDING
Retry: Auto-retry every 30 seconds (5 attempts)
After 5 failed retries: 
  - Alert sent to merchant
  - Manual assignment option appears in admin
  - Customer notified of delay
```

### Scenario 2: Assignment Service Down
```
When: POST /orders/auto-assign times out
Action: Order created but NOT assigned
Status: PENDING (not ASSIGNED)
Recovery: Manual assignment available
Alert: System logs error, alerts admin
```

### Scenario 3: Rider Goes Offline
```
When: Assigned rider becomes offline
Action: Order remains ASSIGNED (rider responsible)
Alert: Admin notified
Options: Admin can reassign if rider doesn't pick up
Timeout: Auto-reassign after 10 min offline
```

---

## Configuration & Environment

### Required Environment Variables
```bash
# Assignment Service Location
ASSIGNMENT_SERVICE_URL=http://localhost:8100

# Tracking Service Location
TRACKING_SERVICE_URL=http://localhost:8300

# Notification Service Location
NOTIFICATION_SERVICE_URL=http://localhost:8400
```

### Optional Tuning Parameters
```python
# In assignment_engine.py
MAX_ACTIVE_ORDERS = 3        # Max orders per rider
MIN_RIDER_RATING = 3.5       # Minimum star rating
MAX_SERVICE_RADIUS_KM = 50   # Max distance to rider
AUTO_RETRY_ATTEMPTS = 5      # Failed assignment retries
AUTO_RETRY_INTERVAL_SEC = 30 # Seconds between retries
```

---

## Service Integration Points

### Order Service ↔ Assignment Service
```
Trigger: POST /orders/create
Called: Immediately after order creation
Timeout: 10 seconds
Failure: Logs warning, order stays PENDING
Response: Returns assigned rider + score breakdown
```

### Assignment Service ↔ Tracking Service
```
Trigger: Auto-assignment success
Called: Via assignment_service main.py
Action: Starts real-time GPS tracking
Session: Continuous until delivery
```

### Order Service ↔ Notification Service
```
Trigger: Order placed event
Called: After order creation
Recipients: Merchant (order confirmation)
Called: After assignment
Recipients: Rider (order details)
```

---

## Monitoring & Metrics

### Key Metrics to Track
```
1. Assignment Success Rate
   - % orders auto-assigned successfully
   - Target: > 95%

2. Assignment Time
   - Avg time from order creation to assignment
   - Target: < 2 seconds

3. Rider Utilization
   - Avg active orders per rider
   - Target: 1.5 - 2.5 orders

4. Score Distribution
   - Avg assignment score
   - Min/Max scores
   - Target: > 0.80 average

5. Retry Rates
   - % orders requiring retry
   - % orders failing after retries
   - Target: < 2% failures
```

### Admin Monitoring Dashboard
```
┌─ Assignment Metrics ────────┐
│                             │
│ Today's Assignments: 145    │
│ Success Rate: 98.6%         │
│ Avg Score: 0.87             │
│ Avg Time: 1.2 sec           │
│                             │
│ Failed Assignments: 2       │
│ Manual Assignments: 0       │
│ System Retries: 3           │
│                             │
└─────────────────────────────┘
```

---

## Troubleshooting Guide

### Issue: Order Stuck in PENDING Status

**Symptoms:**
- Order created but not assigned
- Status = PENDING after 1 minute

**Causes:**
1. No riders online
2. All riders at capacity (3+ orders)
3. Assignment service down
4. Network timeout

**Solution:**
```
1. Check rider status in dashboard
2. Verify assignment service health: GET /health
3. Check service logs for errors
4. If needed: Manual assignment via admin interface
5. Monitor auto-retry attempts
```

### Issue: Order Assigned to Far-Away Rider

**Symptoms:**
- Rider is 20+ km from pickup
- Expected rider 2 km away

**Causes:**
1. All closer riders at capacity
2. Closer riders offline
3. Closer riders have low rating

**Investigation:**
```
Check assignment score breakdown:
- Proximity score: How far is rider?
- Load balance: Other riders available?
- Rating: Closer riders' ratings?
```

### Issue: Same Rider Gets All Orders

**Symptoms:**
- One rider getting 80% of orders
- Other riders idle

**Causes:**
1. Other riders offline
2. Other riders have low rating
3. Load balance scoring not working

**Solution:**
1. Verify all riders online
2. Check rider ratings
3. Review load balance scoring logic
4. Increase MAX_ACTIVE_ORDERS if needed
```

---

## Migration Notes (From Order Pool)

### What Was Removed
- ❌ Manual order pool interface
- ❌ Rider selection dropdown in orders
- ❌ "Accept & Assign" manual button
- ❌ GET /api/company/order_pool endpoint
- ❌ POST /api/company/order_pool/accept endpoint

### What Stays the Same
- ✅ Order creation flow
- ✅ Payment processing
- ✅ Tracking system
- ✅ Notification system
- ✅ Review & rating system
- ✅ Cancellation & refund system

### Admin Responsibilities (Changed)
| Task | Before | After |
|------|--------|-------|
| Assign riders | Manual (5-10 min) | Automatic (< 2 sec) |
| Monitor queue | Active | Passive |
| Handle reassignments | Frequent | Rare (if any) |
| Verify assignments | Manual | Automated |
| Problem resolution | Reactive | Proactive alerts |

---

## Rollback Plan (If Needed)

Should auto-assignment cause issues:

1. **Immediate:** Disable assignment service
   - Set ASSIGNMENT_SERVICE_URL to null
   - Orders will stay PENDING
   - Enable manual assignment fallback

2. **Short-term:** Revert to order pool
   - Restore company.html from backup
   - Restore order_pool endpoints
   - Resume manual assignment process

3. **Root Cause Analysis:** Debug and fix
   - Review assignment logs
   - Check scoring algorithm
   - Test with different parameters
   - Retest before re-enabling

---

## Success Criteria

**✅ Full Auto-Assignment System is considered successful when:**

1. **Reliability**: > 95% of orders auto-assigned successfully
2. **Speed**: Assignment completes in < 2 seconds
3. **Satisfaction**: Merchants report reduced manual work
4. **Quality**: Rider assignments meet proximity + quality standards
5. **Stability**: System uptime > 99.5%
6. **Performance**: No impact on order creation latency

---

## Summary

The **Full Auto-Assignment System** replaces manual order pooling with instant, intelligent rider matching. Orders are automatically assigned to the best available rider using a 5-factor hybrid scoring algorithm, improving speed and reducing operational overhead.

**Key Principles:**
- 🚀 **Fast:** Instant assignment (< 2 sec)
- 🎯 **Smart:** Multi-factor scoring
- 👥 **Fair:** Load-balanced distribution
- 📊 **Transparent:** Score breakdown visible
- 🔧 **Reliable:** Retry logic & error handling

**Result:** Better customer experience, faster order fulfillment, simpler operations.
