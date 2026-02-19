# Backend Integration Testing Guide

## Overview
This guide provides comprehensive instructions for testing the backend services integration with the Rider Mobile App.

## 📋 Testing Phases

### Phase 1: Service Health Verification
Verify all backend services are running and accessible.

**Services to Check**:
1. **API Gateway** - Port 8100
   - Health check: `GET http://localhost:8100/health`
   - Expected response: `{"status": "ok"}`

2. **Order Service** - Port 8500
   - Health check: `GET http://localhost:8500/health`
   - Expected response: `{"status": "ok"}`

3. **Tracking Service** - Port 8300
   - Health check: `GET http://localhost:8300/health`
   - Expected response: `{"status": "ok"}`

4. **Notification Service** - Port 8400
   - Health check: `GET http://localhost:8400/health`
   - Expected response: `{"status": "ok"}`

### Phase 2: API Endpoint Testing

#### Authentication Endpoints
```bash
# Login
POST /api/auth/login
Content-Type: application/json

{
  "email": "rider@example.com",
  "password": "password123"
}

Expected Response (200):
{
  "token": "jwt_token_here",
  "rider": {
    "id": "rider_123",
    "name": "John Rider",
    "email": "rider@example.com",
    "phone": "+919876543210"
  }
}
```

```bash
# Verify OTP
POST /api/auth/verify-otp
Content-Type: application/json

{
  "phone": "+919876543210",
  "otp": "123456"
}

Expected Response (200):
{
  "token": "jwt_token_here",
  "rider": {...}
}
```

#### Order Service Endpoints
```bash
# Get all orders
GET /api/orders
Authorization: Bearer {token}

Expected Response (200):
{
  "orders": [
    {
      "id": "order_123",
      "status": "assigned",
      "customer_id": "cust_123",
      "pickup_location": "Store Address",
      "dropoff_location": "Customer Address",
      "price": 150.00
    }
  ]
}
```

```bash
# Get order details
GET /api/orders/{id}
Authorization: Bearer {token}

Expected Response (200):
{
  "id": "order_123",
  "status": "assigned",
  "customer_id": "cust_123",
  "customer_name": "Customer Name",
  "pickup_location": "Store Address",
  "pickup_lat": 28.7041,
  "pickup_lng": 77.1025,
  "dropoff_location": "Customer Address",
  "dropoff_lat": 28.6139,
  "dropoff_lng": 77.2090,
  "price": 150.00,
  "items": [...]
}
```

```bash
# Update order status
PUT /api/orders/{id}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "picked_up",
  "notes": "Order picked up, on the way"
}

Expected Response (200):
{
  "success": true,
  "message": "Order status updated",
  "order": {...}
}
```

```bash
# Cancel order
POST /api/orders/{id}/cancel
Authorization: Bearer {token}
Content-Type: application/json

{
  "reason": "Unable to deliver",
  "notes": "Customer not available"
}

Expected Response (200):
{
  "success": true,
  "message": "Order cancelled",
  "refund_initiated": true
}
```

#### Tracking Service Endpoints
```bash
# Update location
POST /api/tracking/location
Authorization: Bearer {token}
Content-Type: application/json

{
  "latitude": 28.7041,
  "longitude": 77.1025,
  "accuracy": 10,
  "speed": 15,
  "heading": 180,
  "order_id": "order_123"
}

Expected Response (200):
{
  "success": true,
  "message": "Location updated"
}
```

```bash
# Get tracking info
GET /api/tracking/order/{id}
Authorization: Bearer {token}

Expected Response (200):
{
  "order_id": "order_123",
  "rider_location": {
    "latitude": 28.7041,
    "longitude": 77.1025
  },
  "pickup_location": {
    "latitude": 28.7041,
    "longitude": 77.1025
  },
  "dropoff_location": {
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "distance_to_destination": 5.2,
  "estimated_time": 10
}
```

#### Earnings/Payment Service Endpoints
```bash
# Get earnings summary
GET /api/earnings/summary?period=monthly
Authorization: Bearer {token}

Expected Response (200):
{
  "total_earnings": 5000.00,
  "available_balance": 4500.00,
  "pending_payouts": 500.00,
  "completed_orders": 25,
  "rating": 4.8
}
```

```bash
# Get payout history
GET /api/earnings/payouts
Authorization: Bearer {token}

Expected Response (200):
{
  "payouts": [
    {
      "id": "payout_123",
      "amount": 1000.00,
      "date": "2024-01-20",
      "status": "completed",
      "method": "bank_transfer"
    }
  ]
}
```

```bash
# Request payout
POST /api/earnings/request-payout
Authorization: Bearer {token}
Content-Type: application/json

{
  "amount": 2000.00
}

Expected Response (200):
{
  "success": true,
  "message": "Payout request initiated",
  "payout_id": "payout_124"
}
```

#### Profile Service Endpoints
```bash
# Get rider profile
GET /api/riders/profile
Authorization: Bearer {token}

Expected Response (200):
{
  "id": "rider_123",
  "name": "John Rider",
  "email": "rider@example.com",
  "phone": "+919876543210",
  "avatar": "https://...",
  "rating": 4.8,
  "completed_orders": 25,
  "status": "online"
}
```

```bash
# Update profile
PUT /api/riders/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "John Rider",
  "email": "newemail@example.com",
  "phone": "+919876543211"
}

Expected Response (200):
{
  "success": true,
  "message": "Profile updated",
  "rider": {...}
}
```

```bash
# Update status (online/offline)
POST /api/riders/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "online"
}

Expected Response (200):
{
  "success": true,
  "status": "online"
}
```

## 🧪 Running Integration Tests

### Using Test Script
```bash
chmod +x backend_integration_test.sh
./backend_integration_test.sh
```

### Manual Testing with cURL
```bash
# Health check
curl -s http://localhost:8100/health | jq

# Login (get token)
curl -X POST http://localhost:8100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"rider@example.com","password":"password123"}' | jq

# Get orders (requires token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8100/api/orders | jq
```

### Using Postman
1. Import the API endpoints
2. Create environment variables:
   - `BASE_URL`: http://localhost:8100
   - `TOKEN`: (obtained from login)
3. Create test collection:
   - Authentication tests
   - Order flow tests
   - Tracking tests
   - Earnings tests
   - Profile tests

## ✅ Test Coverage

### Critical Paths to Test
- [ ] User Login/Registration
- [ ] Order List Display
- [ ] Order Details Retrieval
- [ ] Status Update Flow
- [ ] Order Cancellation
- [ ] Location Tracking Updates
- [ ] Earnings Summary Retrieval
- [ ] Payout Request
- [ ] Profile Display
- [ ] Profile Update
- [ ] Online/Offline Toggle

### Edge Cases
- [ ] Network timeout handling
- [ ] Invalid token handling
- [ ] Concurrent requests
- [ ] Rapid location updates
- [ ] Order status conflicts
- [ ] Missing/invalid data
- [ ] Permission errors

## 🔍 Debugging

### Check Service Logs
```bash
# API Gateway logs
docker logs api_gateway

# Order Service logs
docker logs order_service

# Tracking Service logs
docker logs tracking_service

# Notification Service logs
docker logs notification_service
```

### Common Issues

**Issue**: Connection refused on port 8100
**Solution**: Start API Gateway service
```bash
cd services/api_gateway
python main.py
```

**Issue**: Authentication token invalid
**Solution**: Ensure token is properly passed in Authorization header
```
Authorization: Bearer {token}
```

**Issue**: CORS errors
**Solution**: Check CORS configuration in FastAPI services
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Issue**: Database connection errors
**Solution**: Verify PostgreSQL is running and schema is initialized
```bash
python init_db.py
```

## 📊 Performance Testing

### Load Testing with Apache Bench
```bash
# Test order list endpoint
ab -n 100 -c 10 http://localhost:8100/api/orders

# Test location update endpoint
ab -n 1000 -c 50 -p location.json \
  -H "Authorization: Bearer {token}" \
  http://localhost:8300/api/tracking/location
```

### Response Time Benchmarks (Target)
- Authentication: < 500ms
- Order List: < 1000ms
- Order Details: < 500ms
- Location Update: < 200ms
- Status Update: < 500ms

## 🔐 Security Testing

### Test Cases
- [ ] SQL Injection prevention
- [ ] XSS protection
- [ ] CSRF token validation
- [ ] Rate limiting
- [ ] Input validation
- [ ] Authorization checks
- [ ] Data encryption (HTTPS)

### Command Examples
```bash
# Test SQL Injection prevention
curl -X POST http://localhost:8100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"` OR 1=1 --","password":"*"}'

# Test invalid token
curl -H "Authorization: Bearer invalid_token" \
  http://localhost:8100/api/orders
```

## 📈 Test Metrics

### Success Criteria
- All services return HTTP 200 on health check
- Authentication endpoints return valid JWT tokens
- Order endpoints return complete order data
- Tracking updates are processed < 200ms
- No connection errors for 1000+ requests
- All responses contain expected data structure

### Failure Handling
- Graceful error responses (HTTP 4xx, 5xx)
- Meaningful error messages
- Proper error codes and statuses
- No sensitive data in error messages

## 📝 Test Report Template

```
Testing Date: [DATE]
Tested By: [NAME]
Environment: [dev/staging/prod]

Test Results:
- Health Checks: [PASS/FAIL]
- Authentication: [PASS/FAIL]
- Order Services: [PASS/FAIL]
- Tracking: [PASS/FAIL]
- Earnings: [PASS/FAIL]
- Profile: [PASS/FAIL]

Issues Found:
1. [Issue Description]
   - Severity: [Critical/High/Medium/Low]
   - Steps to Reproduce: [...]
   - Expected: [...]
   - Actual: [...]
   - Fix: [...]

Performance Results:
- Average Response Time: [ms]
- Slowest Endpoint: [...]
- Fastest Endpoint: [...]

Notes:
[Any additional observations]
```

## 🚀 Next Steps

1. **Start Services**: Ensure all backend services are running
2. **Run Health Checks**: Verify all services are accessible
3. **Run Integration Tests**: Execute test script or manual tests
4. **Document Issues**: Record any failures or inconsistencies
5. **Fix Issues**: Address any identified problems
6. **Re-test**: Verify fixes work correctly
7. **Load Testing**: Stress test critical endpoints
8. **Security Testing**: Validate security measures
9. **Deploy**: Push to production once all tests pass

## 📞 Support

For issues or questions:
1. Check backend service logs
2. Verify network connectivity
3. Ensure database is initialized
4. Check API configuration matches app settings
5. Review error messages for clues

---

**Status**: Ready for Backend Integration Testing
**Last Updated**: January 31, 2024
