# Quick Reference: Rate Limiting & Order State Machine

## Rate Limiting Quick Reference

### Import & Use

```python
from shared.security import check_rate_limit, get_client_ip, auth_limiter, api_limiter, public_limiter
from fastapi import Request

@app.post("/endpoint")
async def my_endpoint(req: Request):
    # Check rate limit
    client_id = get_client_ip(req)
    if not check_rate_limit(client_id, auth_limiter):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Process request...
```

### Rate Limit Tiers

| Limiter | Rate | Use Case |
|---------|------|----------|
| `auth_limiter` | 5/min | register, login |
| `public_limiter` | 20/min | booking, health checks |
| `api_limiter` | 100/min | internal APIs |

### Response

```json
HTTP 429 Too Many Requests
{
    "detail": "Too many [action] attempts. Please try again later."
}
```

---

## Order State Machine Quick Reference

### State Diagram

```
PENDING ──→ ASSIGNED ──→ PICKED_UP ──→ IN_TRANSIT ──→ DELIVERED
    ↓           ↓            ↓             ↓
CANCELLED   CANCELLED    CANCELLED     CANCELLED
```

### Valid Transitions

```python
PENDING      → ASSIGNED, CANCELLED
ASSIGNED     → PICKED_UP, CANCELLED
PICKED_UP    → IN_TRANSIT, CANCELLED
IN_TRANSIT   → DELIVERED, CANCELLED
DELIVERED    → (terminal)
CANCELLED    → (terminal)
```

### API Endpoints

```bash
# Create (PENDING)
POST /orders/create

# Assign (PENDING → ASSIGNED)
POST /orders/{order_id}/assign

# Update (PICKED_UP, IN_TRANSIT, DELIVERED, CANCELLED)
POST /orders/{order_id}/status

# Get & List
GET /orders/{order_id}
GET /orders?status=assigned
```

### Error Response

```json
HTTP 400 Bad Request
{
    "detail": "Cannot transition from pending to delivered. Allowed transitions: [assigned, cancelled]"
}
```

---

## Testing Snippets

### Test Rate Limiting

```bash
# Rapid requests (should fail after limit)
for i in {1..10}; do
  curl -X POST http://localhost:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username":"user","password":"pass"}' \
    -w " → HTTP %{http_code}\n"
done
```

### Test State Machine

```bash
# Invalid transition
curl -X POST http://localhost:8500/orders/order123/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "delivered"}' # Invalid from PENDING!

# Expected: HTTP 400 with helpful message
```

---

## Configuration

### Modify Rate Limits

In `/shared/security.py`:

```python
# Change public limiter to 50 requests per 60 seconds
public_limiter = RateLimiter(max_requests=50, window_seconds=60)

# Change auth limiter to 3 requests per 60 seconds  
auth_limiter = RateLimiter(max_requests=3, window_seconds=60)
```

### Add Custom Limiter

```python
# For a specific endpoint
custom_limiter = RateLimiter(max_requests=10, window_seconds=30)

@app.post("/expensive-endpoint")
async def expensive(req: Request):
    if not check_rate_limit(get_client_ip(req), custom_limiter):
        raise HTTPException(status_code=429)
```

---

## Monitoring

### Check Rate Limit Status

```python
# Number of requests from a client
limiter.requests[client_id]  # List of timestamps

# Clear limiter (admin)
limiter.requests.clear()

# Check if allowed
is_allowed = check_rate_limit(client_id, limiter)
```

### Log Rate Limit Hits

```python
# Add to auth_service or order_service
import logging
logger = logging.getLogger(__name__)

if not check_rate_limit(client_id, auth_limiter):
    logger.warning(f"Rate limit exceeded for {client_id}")
    raise HTTPException(status_code=429)
```

---

## Common Errors & Solutions

### "Too many registration attempts"
- **Cause**: Client exceeded 5 registrations per minute
- **Solution**: Wait 60 seconds, try again

### "Cannot transition from pending to delivered"
- **Cause**: Trying to skip intermediate states
- **Solution**: Follow the valid path: pending → assigned → picked_up → in_transit → delivered

### "Only the assigned rider can update order status"
- **Cause**: Wrong user trying to update order
- **Solution**: Use the rider's token who is assigned to the order

---

## File Locations

- **Rate Limiting**: `/shared/security.py`
- **Order Service**: `/services/order_service/main.py`
- **Auth Service**: `/services/auth_service/main.py`
- **Full Documentation**: `/RATE_LIMITING_AND_ORDER_STATE_MACHINE.md`

---

## Environment Setup

```bash
# Install dependencies
pip install -r requirements-db.txt

# Set environment variables
export JWT_SECRET="your-secret-key"
export DATABASE_URL="postgresql://user:pass@localhost/deliverydb"
export TRACKING_SERVICE_URL="http://localhost:8300"
export NOTIFICATION_SERVICE_URL="http://localhost:8400"

# Run services
python services/order_service/main.py
python services/auth_service/main.py
```

---

## Key Takeaways

✅ **Rate Limiting**: Protects auth endpoints from brute force attacks
✅ **State Machine**: Ensures orders follow proper workflow, prevents data corruption
✅ **Distributed**: Rate limiter tracks per-client IP across all requests
✅ **Stateful**: Order states persisted to PostgreSQL, survives service restarts
✅ **Observable**: Clear error messages aid debugging and monitoring
