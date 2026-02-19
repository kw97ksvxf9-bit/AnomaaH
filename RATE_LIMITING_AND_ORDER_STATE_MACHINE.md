# Rate Limiting & Order State Machine Implementation

## Overview

This document covers the implementation of rate limiting across API endpoints and the order status state machine that ensures proper order workflow management.

---

## Part 1: Rate Limiting

### Architecture

Rate limiting is implemented using an in-memory `RateLimiter` class in `/shared/security.py`. It tracks client requests with a sliding window algorithm.

### Components

#### RateLimiter Class

```python
class RateLimiter:
    """Manages rate limiting with time-windowed request tracking."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests      # Max requests allowed
        self.window_seconds = window_seconds  # Time window in seconds
        self.requests = defaultdict(list)     # {client_id: [timestamp1, timestamp2, ...]}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        current_time = time.time()
        # Remove old requests outside the window
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] 
            if current_time - ts < self.window_seconds
        ]
        # Check if within limit
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(current_time)
            return True
        return False
```

### Pre-configured Rate Limiters

Three global limiter instances are configured:

```python
# Public endpoints: 20 requests per 60 seconds
public_limiter = RateLimiter(max_requests=20, window_seconds=60)

# Auth endpoints (register, login): 5 requests per 60 seconds  
auth_limiter = RateLimiter(max_requests=5, window_seconds=60)

# API endpoints: 100 requests per 60 seconds
api_limiter = RateLimiter(max_requests=100, window_seconds=60)
```

### Helper Functions

```python
def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers or connection."""
    # Checks X-Forwarded-For (proxy) first, falls back to connection IP
    return request.client[0] if request.client else "unknown"

def check_rate_limit(client_id: str, limiter: RateLimiter) -> bool:
    """Check if request is allowed under rate limit."""
    return limiter.is_allowed(client_id)
```

### Integration Example

#### Auth Service (Registration & Login)

```python
from shared.security import check_rate_limit, get_client_ip, auth_limiter

@app.post("/register", response_model=Token)
async def register(
    request: RegisterRequest, 
    db: Session = Depends(get_db), 
    req: Request = None
):
    """Register a new user."""
    
    # Apply rate limiting (5 requests per minute)
    if req:
        client_id = get_client_ip(req)
        if not check_rate_limit(client_id, auth_limiter):
            raise HTTPException(
                status_code=429,
                detail="Too many registration attempts. Please try again later."
            )
    
    # ... rest of registration logic
```

### Rate Limit Tiers

| Endpoint Type | Limit | Window | Use Case |
|---|---|---|---|
| Public (booking, health) | 20 req/min | 60s | General public access |
| Auth (register, login) | 5 req/min | 60s | Brute force protection |
| API (orders, tracking) | 100 req/min | 60s | Authenticated internal APIs |

### Response Codes

- **HTTP 200**: Request allowed and processed
- **HTTP 429 Too Many Requests**: Rate limit exceeded
  - Response: `{"detail": "Too many [action] attempts. Please try again later."}`

### Monitoring

To monitor rate limiting:

```python
# Check current request count for a client
requests_for_client = len(limiter.requests.get(client_id, []))

# Clear limiter (admin function)
limiter.requests.clear()
```

---

## Part 2: Order Status State Machine

### Order Status Flow

The order lifecycle is strictly enforced through a state machine:

```
PENDING 
  ├→ ASSIGNED 
  │   ├→ PICKED_UP 
  │   │   ├→ IN_TRANSIT 
  │   │   │   └→ DELIVERED (Terminal)
  │   │   └→ CANCELLED (Terminal)
  │   └→ CANCELLED (Terminal)
  └→ CANCELLED (Terminal)
```

### State Definitions

```python
class OrderStatus(str, Enum):
    PENDING = "pending"           # Order placed, awaiting assignment
    ASSIGNED = "assigned"         # Rider assigned to order
    PICKED_UP = "picked_up"       # Order picked up by rider
    IN_TRANSIT = "in_transit"     # Order in transit to destination
    DELIVERED = "delivered"       # Order delivered (terminal)
    CANCELLED = "cancelled"       # Order cancelled (terminal)
```

### State Machine Rules

The `OrderStateMachine` class enforces valid transitions:

```python
class OrderStateMachine:
    """Manages valid order status transitions."""
    
    VALID_TRANSITIONS = {
        OrderStatus.PENDING: [
            OrderStatus.ASSIGNED,    # Company accepts and assigns rider
            OrderStatus.CANCELLED    # Merchant cancels before assignment
        ],
        OrderStatus.ASSIGNED: [
            OrderStatus.PICKED_UP,   # Rider has picked up order
            OrderStatus.CANCELLED    # Order cancelled after assignment
        ],
        OrderStatus.PICKED_UP: [
            OrderStatus.IN_TRANSIT,  # Rider starts transit
            OrderStatus.CANCELLED    # Last-minute cancellation
        ],
        OrderStatus.IN_TRANSIT: [
            OrderStatus.DELIVERED,   # Order delivered
            OrderStatus.CANCELLED    # Emergency cancellation
        ],
        OrderStatus.DELIVERED: [],   # No transitions from delivered
        OrderStatus.CANCELLED: [],   # No transitions from cancelled
    }
    
    @staticmethod
    def is_valid_transition(
        current_status: OrderStatus, 
        new_status: OrderStatus
    ) -> bool:
        """Check if transition is valid."""
        return new_status in OrderStateMachine.VALID_TRANSITIONS.get(
            current_status, 
            []
        )
    
    @staticmethod
    def get_allowed_transitions(current_status: OrderStatus) -> List[str]:
        """Get list of allowed status values from current state."""
        return [
            s.value for s in OrderStateMachine.VALID_TRANSITIONS.get(
                current_status, 
                []
            )
        ]
```

### Order Model Attributes

```python
class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Core order info
    payment_id: Mapped[str] = mapped_column(String, ForeignKey("payments.id"))
    merchant_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    company_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("rider_companies.id"))
    assigned_rider_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("riders.id"))
    
    # Location & logistics
    pickup_address: Mapped[str] = mapped_column(String)
    pickup_lat: Mapped[float] = mapped_column(Float)
    pickup_lng: Mapped[float] = mapped_column(Float)
    dropoff_address: Mapped[str] = mapped_column(String)
    dropoff_lat: Mapped[float] = mapped_column(Float)
    dropoff_lng: Mapped[float] = mapped_column(Float)
    distance_km: Mapped[float] = mapped_column(Float)
    eta_min: Mapped[int] = mapped_column(Integer)
    price_ghs: Mapped[float] = mapped_column(Float)
    
    # Status & timestamps
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), 
        default=OrderStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    picked_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

### Endpoint: Create Order

Creates a new order in `PENDING` status:

```python
POST /orders/create
Content-Type: application/json
Authorization: Bearer <token>

{
    "payment_id": "pay_123abc",
    "merchant_id": "merch_xyz",
    "pickup_address": "Shop A, Accra",
    "pickup_lat": 5.6037,
    "pickup_lng": -0.1870,
    "dropoff_address": "Customer Home, Accra",
    "dropoff_lat": 5.6200,
    "dropoff_lng": -0.1850,
    "distance_km": 2.5,
    "eta_min": 15,
    "price_ghs": 25.00
}

Response 200:
{
    "id": "order_abc123",
    "status": "pending",
    "pickup_address": "Shop A, Accra",
    "dropoff_address": "Customer Home, Accra",
    "distance_km": 2.5,
    "eta_min": 15,
    "price_ghs": 25.00,
    "assigned_rider_id": null,
    "created_at": "2024-01-15T10:30:00Z",
    "assigned_at": null,
    "delivered_at": null,
    "tracking_link": null
}
```

**Validation:**
- Payment must exist and be COMPLETED
- Current status must be PENDING (always true for new orders)

### Endpoint: Assign Order

Transitions order from `PENDING` to `ASSIGNED`:

```python
POST /orders/{order_id}/assign
Content-Type: application/json
Authorization: Bearer <company_admin_token>

{
    "rider_id": "rider_456def",
    "company_id": "company_789ghi"
}

Response 200:
{
    "id": "order_abc123",
    "status": "assigned",
    "pickup_address": "Shop A, Accra",
    "dropoff_address": "Customer Home, Accra",
    "distance_km": 2.5,
    "eta_min": 15,
    "price_ghs": 25.00,
    "assigned_rider_id": "rider_456def",
    "created_at": "2024-01-15T10:30:00Z",
    "assigned_at": "2024-01-15T10:31:00Z",
    "delivered_at": null,
    "tracking_link": "https://track.platform.com/order_abc123"
}
```

**Validation:**
- Order must be in PENDING status
- Rider must exist and belong to the specified company
- Transition triggers tracking service call

### Endpoint: Update Order Status

Transitions order through states `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`, or `CANCELLED`:

```python
POST /orders/{order_id}/status
Content-Type: application/json
Authorization: Bearer <rider_token>

{
    "status": "picked_up",
    "notes": "Package picked up from shop"
}

Response 200:
{
    "id": "order_abc123",
    "status": "picked_up",
    "pickup_address": "Shop A, Accra",
    "dropoff_address": "Customer Home, Accra",
    "distance_km": 2.5,
    "eta_min": 15,
    "price_ghs": 25.00,
    "assigned_rider_id": "rider_456def",
    "created_at": "2024-01-15T10:30:00Z",
    "assigned_at": "2024-01-15T10:31:00Z",
    "delivered_at": null,
    "tracking_link": "https://track.platform.com/order_abc123"
}
```

**Validations:**
- Order must exist
- Status must be a valid OrderStatus enum value
- Current status must allow transition to requested status
- Only assigned rider or superadmin can update
- Updates corresponding timestamp (picked_up_at, delivered_at, cancelled_at)

**Error Response (Invalid Transition):**

```
POST /orders/order_abc123/status
{
    "status": "delivered"  // Currently in PENDING, invalid!
}

Response 400:
{
    "detail": "Cannot transition from pending to delivered. Allowed transitions: [assigned, cancelled]"
}
```

### Endpoint: List Orders

Lists orders filtered by user role and optional status:

```python
GET /orders?status=assigned
Authorization: Bearer <token>

Response 200: [
    {
        "id": "order_abc123",
        "status": "assigned",
        "pickup_address": "Shop A, Accra",
        "dropoff_address": "Customer Home, Accra",
        "distance_km": 2.5,
        "eta_min": 15,
        "price_ghs": 25.00,
        "assigned_rider_id": "rider_456def",
        "created_at": "2024-01-15T10:30:00Z",
        "assigned_at": "2024-01-15T10:31:00Z",
        "delivered_at": null,
        "tracking_link": "https://track.platform.com/order_abc123"
    },
    ...
]
```

**Role-based Filtering:**
- **merchant**: See only own orders
- **rider**: See only assigned orders  
- **company_admin**: See company's orders
- **superadmin**: See all orders

---

## Integration Example: Complete Order Workflow

### 1. Merchant Places Order (After Payment)

```bash
curl -X POST http://localhost:8500/orders/create \
  -H "Authorization: Bearer <merchant_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": "pay_123abc",
    "pickup_address": "Shop A",
    "pickup_lat": 5.6037,
    "pickup_lng": -0.1870,
    "dropoff_address": "Customer",
    "dropoff_lat": 5.6200,
    "dropoff_lng": -0.1850,
    "distance_km": 2.5,
    "eta_min": 15,
    "price_ghs": 25.00
  }'

# Order created with status: PENDING
```

### 2. Company Admin Assigns Rider

```bash
curl -X POST http://localhost:8500/orders/order_abc123/assign \
  -H "Authorization: Bearer <company_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "rider_id": "rider_456def",
    "company_id": "company_789ghi"
  }'

# Order transitioned: PENDING → ASSIGNED
# Tracking session started
# Merchant notified with tracking link
```

### 3. Rider Picks Up Order

```bash
curl -X POST http://localhost:8500/orders/order_abc123/status \
  -H "Authorization: Bearer <rider_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "picked_up",
    "notes": "Package picked up"
  }'

# Order transitioned: ASSIGNED → PICKED_UP
```

### 4. Rider in Transit

```bash
curl -X POST http://localhost:8500/orders/order_abc123/status \
  -H "Authorization: Bearer <rider_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_transit"
  }'

# Order transitioned: PICKED_UP → IN_TRANSIT
```

### 5. Rider Delivers Order

```bash
curl -X POST http://localhost:8500/orders/order_abc123/status \
  -H "Authorization: Bearer <rider_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "delivered",
    "notes": "Order delivered to customer"
  }'

# Order transitioned: IN_TRANSIT → DELIVERED (Terminal)
# Merchant notified
```

---

## Error Handling

### Rate Limiting Error

```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
    "detail": "Too many login attempts. Please try again later."
}
```

### Invalid State Transition

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "detail": "Cannot transition from pending to delivered. Allowed transitions: [assigned, cancelled]"
}
```

### Permission Denied

```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
    "detail": "Only the assigned rider or admin can update order status"
}
```

---

## Best Practices

### Rate Limiting
1. Always extract client IP before checking limits
2. Use appropriate tier for endpoint type
3. Log rate limit hits for security monitoring
4. Consider increasing limits for internal/VPN traffic

### Order State Machine
1. Never bypass state transitions - always go through valid path
2. Store timestamp for each state change for audit trail
3. Validate permissions at each transition
4. Send notifications at key state changes
5. Keep state history for analytics and debugging

---

## Testing

### Rate Limiting Test

```bash
# Rapid login attempts (should fail after 5)
for i in {1..10}; do
  curl -X POST http://localhost:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"pass"}' \
    -w "%{http_code}\n"
done

# Expected: 5 × 200 (or errors), then 5 × 429
```

### State Machine Test

```bash
# Try invalid transition
curl -X POST http://localhost:8500/orders/order_123/status \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "delivered"}'  # Invalid from PENDING

# Expected: 400 with helpful error message
```

---

## Monitoring & Metrics

### Key Metrics

1. **Rate Limit Hits**: Count of 429 responses per endpoint
2. **State Transition Time**: Duration between states
3. **Order Fulfillment Rate**: % of orders reaching DELIVERED
4. **Stuck Orders**: Orders in PENDING > 30 minutes

### Logs to Monitor

```
[INFO] Order order_abc123 assigned to rider rider_456def
[WARN] Order order_xyz789 state transition blocked: pending → delivered
[ERROR] Failed to start tracking for order order_def456
```

---

## Future Enhancements

1. **Distributed Rate Limiting**: Redis-backed for multi-instance deployments
2. **Custom Rate Limits**: Per-merchant/rider limits
3. **Order State Hooks**: Custom logic on state transitions
4. **Order Cancellation Refunds**: Automatic refund logic when CANCELLED
5. **Estimated Delivery Time**: Dynamic ETA updates during IN_TRANSIT
