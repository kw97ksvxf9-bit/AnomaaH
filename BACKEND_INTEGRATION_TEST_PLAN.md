# Backend Integration Testing - Execution Plan

## 📋 Pre-Testing Checklist

### System Requirements
- [ ] All backend services running
- [ ] PostgreSQL database initialized
- [ ] Redis cache available (if needed)
- [ ] Network connectivity verified
- [ ] API Base URL: http://localhost:8100
- [ ] Android emulator/device ready
- [ ] Build config verified

### Verify Backend Services
```bash
# Check API Gateway
curl -s http://localhost:8100/health | jq

# Check Order Service
curl -s http://localhost:8500/health | jq

# Check Tracking Service
curl -s http://localhost:8300/health | jq

# Check Notification Service
curl -s http://localhost:8400/health | jq
```

---

## 🧪 Phase 1: API Endpoint Testing

### 1.1 Authentication Flow

**Test Case 1.1.1: User Login**
```bash
curl -X POST http://localhost:8100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "rider@example.com",
    "password": "password123"
  }'

Expected Response:
- Status: 200 OK
- Contains: token, rider_id, name, email, phone
- Token is valid JWT format
```

**Test Case 1.1.2: OTP Verification**
```bash
curl -X POST http://localhost:8100/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "otp": "123456"
  }'

Expected Response:
- Status: 200 OK
- Contains: token, rider_id
- Token can be used for subsequent calls
```

**Test Case 1.1.3: Logout**
```bash
curl -X POST http://localhost:8100/api/auth/logout \
  -H "Authorization: Bearer {token}"

Expected Response:
- Status: 200 OK
- Token should be invalidated
```

### Verification Checklist
- [ ] Login returns valid token
- [ ] Token included in subsequent requests
- [ ] OTP verification works
- [ ] Logout invalidates token
- [ ] Invalid credentials return 401
- [ ] Missing fields return 400

---

## 🎯 Phase 2: Order Management Testing

### 2.1 Get Orders List

**Test Case 2.1.1: Retrieve Rider Orders**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8100/api/orders/rider/{rider_id}

Expected Response:
- Status: 200 OK
- Array of order objects
- Each order contains: id, status, customer, locations, price
- Status codes: assigned, picked_up, in_transit, delivered
```

**Test Case 2.1.2: Filter by Status**
```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8100/api/orders/rider/{rider_id}?status=assigned"

Expected Response:
- Status: 200 OK
- Only orders with status=assigned
```

### 2.2 Get Order Details

**Test Case 2.2.1: Retrieve Single Order**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8100/api/orders/{order_id}

Expected Response:
- Status: 200 OK
- Complete order information:
  - id, status, created_at
  - customer_id, customer_name, phone
  - pickup: location, latitude, longitude
  - dropoff: location, latitude, longitude
  - price, items, special_instructions
  - created_at, updated_at
```

**Test Case 2.2.2: Invalid Order ID**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8100/api/orders/invalid_id

Expected Response:
- Status: 404 Not Found
- Error message: "Order not found"
```

### 2.3 Update Order Status

**Test Case 2.3.1: Mark Order as Picked Up**
```bash
curl -X PUT http://localhost:8100/api/orders/{order_id}/status \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "picked_up",
    "notes": "Order picked up successfully"
  }'

Expected Response:
- Status: 200 OK
- Updated order object with new status
- Notification sent to customer
- Tracking initiated
```

**Test Case 2.3.2: Mark Order as In Transit**
```bash
curl -X PUT http://localhost:8100/api/orders/{order_id}/status \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_transit",
    "notes": "On the way"
  }'

Expected Response:
- Status: 200 OK
- Status updated to in_transit
- Real-time tracking available
```

**Test Case 2.3.3: Mark Order as Delivered**
```bash
curl -X PUT http://localhost:8100/api/orders/{order_id}/status \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "delivered",
    "notes": "Delivered successfully"
  }'

Expected Response:
- Status: 200 OK
- Status updated to delivered
- Earnings credited
- Order moved to completed list
```

### 2.4 Cancel Order

**Test Case 2.4.1: Cancel Active Order**
```bash
curl -X POST http://localhost:8100/api/orders/{order_id}/cancel \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Unable to deliver",
    "notes": "Customer not reachable"
  }'

Expected Response:
- Status: 200 OK
- Status changed to cancelled
- Refund initiated
- Customer notified
```

**Test Case 2.4.2: Cancel Completed Order (should fail)**
```bash
curl -X POST http://localhost:8100/api/orders/{order_id}/cancel \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Customer request"}'

Expected Response:
- Status: 400 Bad Request
- Error: "Cannot cancel completed order"
```

### Verification Checklist
- [ ] Orders list retrieved successfully
- [ ] Order details display all information
- [ ] Status updates work correctly
- [ ] Cancellation triggers refund
- [ ] Customer notifications sent
- [ ] Invalid orders return 404
- [ ] Unauthorized requests return 401

---

## 📍 Phase 3: Tracking Integration

### 3.1 Location Updates

**Test Case 3.1.1: Start Tracking**
```bash
curl -X POST http://localhost:8300/api/tracking/start \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}",
    "rider_id": "{rider_id}"
  }'

Expected Response:
- Status: 200 OK
- Tracking session started
- WebSocket connection available for real-time updates
```

**Test Case 3.1.2: Update Location**
```bash
curl -X POST http://localhost:8300/api/tracking/location \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "{order_id}",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "accuracy": 10,
    "speed": 25,
    "heading": 180,
    "timestamp": "2024-01-31T12:00:00Z"
  }'

Expected Response:
- Status: 200 OK
- Location stored in database
- WebSocket broadcast to customer
- Distance to destination calculated
```

**Test Case 3.1.3: Stop Tracking**
```bash
curl -X POST http://localhost:8300/api/tracking/stop \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"order_id": "{order_id}"}'

Expected Response:
- Status: 200 OK
- Tracking session ended
- Final location recorded
```

### 3.2 Get Tracking Information

**Test Case 3.2.1: Retrieve Tracking Data**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8300/api/tracking/order/{order_id}

Expected Response:
- Status: 200 OK
- Current rider location (lat, lng)
- Pickup location (lat, lng)
- Dropoff location (lat, lng)
- Distance to destination
- Estimated time of arrival
- Real-time tracking status
```

### Verification Checklist
- [ ] Location updates stored correctly
- [ ] Distance calculations accurate
- [ ] ETA updates in real-time
- [ ] Tracking available during delivery
- [ ] WebSocket broadcasts work
- [ ] Accuracy values processed
- [ ] Location history maintained

---

## 💰 Phase 4: Earnings & Payments

### 4.1 Get Earnings Summary

**Test Case 4.1.1: Monthly Earnings**
```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8100/api/earnings/{rider_id}?period=monthly"

Expected Response:
- Status: 200 OK
- total_earnings: 5000.00
- available_balance: 4500.00
- pending_payouts: 500.00
- completed_orders: 25
- rating: 4.8
```

**Test Case 4.1.2: Different Periods**
```bash
# Daily earnings
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8100/api/earnings/{rider_id}?period=daily"

# Weekly earnings
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8100/api/earnings/{rider_id}?period=weekly"

# Yearly earnings
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8100/api/earnings/{rider_id}?period=yearly"

Expected: Correct aggregations for each period
```

### 4.2 Get Payout History

**Test Case 4.2.1: Retrieve Payouts**
```bash
curl -H "Authorization: Bearer {token}" \
  "http://localhost:8100/api/payouts/{rider_id}?limit=20"

Expected Response:
- Status: 200 OK
- Array of payout records
- Each contains: id, amount, date, status, method
- Sorted by date (newest first)
```

### 4.3 Request Payout

**Test Case 4.3.1: Valid Payout Request**
```bash
curl -X POST http://localhost:8100/api/payouts/request \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rider_id": "{rider_id}",
    "amount": 2000.00
  }'

Expected Response:
- Status: 200 OK
- Payout initiated
- Amount deducted from available balance
- Payout marked as pending
```

**Test Case 4.3.2: Insufficient Balance (should fail)**
```bash
curl -X POST http://localhost:8100/api/payouts/request \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000.00}'

Expected Response:
- Status: 400 Bad Request
- Error: "Insufficient balance"
```

### Verification Checklist
- [ ] Earnings calculations correct
- [ ] Period filtering works
- [ ] Payout history accurate
- [ ] Payout requests processed
- [ ] Balance validations enforced
- [ ] Transaction history maintained

---

## 👤 Phase 5: Profile Management

### 5.1 Get Profile

**Test Case 5.1.1: Retrieve Rider Profile**
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8100/api/riders/profile

Expected Response:
- Status: 200 OK
- id, name, email, phone
- avatar_url
- rating, completed_orders
- status (online/offline)
- created_at, updated_at
```

### 5.2 Update Profile

**Test Case 5.2.1: Update Name**
```bash
curl -X PUT http://localhost:8100/api/riders/profile \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Updated"
  }'

Expected Response:
- Status: 200 OK
- Updated profile with new name
```

**Test Case 5.2.2: Update Email**
```bash
curl -X PUT http://localhost:8100/api/riders/profile \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com"
  }'

Expected Response:
- Status: 200 OK
- Email updated
- Verification may be required
```

### 5.3 Update Status

**Test Case 5.3.1: Go Online**
```bash
curl -X POST http://localhost:8100/api/riders/status \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"status": "online"}'

Expected Response:
- Status: 200 OK
- Status updated to online
- Available for order assignment
```

**Test Case 5.3.2: Go Offline**
```bash
curl -X POST http://localhost:8100/api/riders/status \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"status": "offline"}'

Expected Response:
- Status: 200 OK
- Status updated to offline
- No new orders assigned
```

### Verification Checklist
- [ ] Profile data retrieved correctly
- [ ] Name updates work
- [ ] Email updates work
- [ ] Status changes propagate
- [ ] Unauthorized updates rejected
- [ ] Data validation enforced

---

## 🔄 Phase 6: Complete Flow Integration Test

### Scenario: Complete Delivery Flow

**Step 1: Login**
- User logs in with credentials
- Receives JWT token
- Token stored in app

**Step 2: View Orders**
- Fetch orders list
- Display available deliveries
- Show order details on click

**Step 3: Accept Order**
- Mark as picked_up
- Start tracking
- Send notification to customer

**Step 4: Delivery in Progress**
- Update location every 5 seconds
- Calculate distance
- Show real-time progress

**Step 5: Complete Delivery**
- Mark as delivered
- Stop tracking
- Earnings credited

**Step 6: View Earnings**
- Check updated earnings
- Request payout if needed

### Test Execution
```bash
# Run complete flow test
./complete_flow_test.sh
```

### Expected Outcomes
- All API calls return expected responses
- Data consistency maintained
- No errors or timeouts
- Notifications sent correctly
- Earnings updated accurately

---

## 📊 Performance Testing

### Load Test: Order List (100 concurrent users)
```bash
ab -n 100 -c 10 \
  -H "Authorization: Bearer {token}" \
  http://localhost:8100/api/orders/rider/{rider_id}

Expected:
- Avg response time: < 1000ms
- Failed requests: 0
- Requests per second: > 10
```

### Load Test: Location Updates (1000 requests)
```bash
ab -n 1000 -c 50 -p location.json \
  -H "Authorization: Bearer {token}" \
  http://localhost:8300/api/tracking/location

Expected:
- Avg response time: < 200ms
- Failed requests: 0
- p99 latency: < 500ms
```

---

## 🐛 Debugging & Troubleshooting

### Common Issues & Solutions

**Issue 1: Connection Refused**
```
Error: Connection refused on port 8100
Solution:
- Verify service is running: ps aux | grep api_gateway
- Check port: lsof -i :8100
- Start service: python services/api_gateway/main.py
```

**Issue 2: Authentication Failed**
```
Error: 401 Unauthorized
Solution:
- Verify token format: Authorization: Bearer {token}
- Check token expiration
- Re-login to get fresh token
```

**Issue 3: Invalid JSON Response**
```
Error: JSON decode error
Solution:
- Check response headers
- Verify endpoint URL
- Check request body format
```

**Issue 4: Database Connection Error**
```
Error: Cannot connect to database
Solution:
- Verify PostgreSQL running: psql -U postgres
- Initialize schema: python init_db.py
- Check connection string in .env
```

### Logs to Check
```bash
# API Gateway logs
tail -f logs/api_gateway.log

# Order Service logs
tail -f logs/order_service.log

# Database logs
tail -f /var/log/postgresql/postgresql.log

# Application logs
tail -f logs/app.log
```

---

## ✅ Test Sign-Off

### Test Completion Criteria
- [ ] All health checks pass
- [ ] Authentication works
- [ ] Order CRUD operations complete
- [ ] Status updates function correctly
- [ ] Tracking integration works
- [ ] Earnings calculations accurate
- [ ] Profile management operational
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] Error handling proper

### Sign-Off
- **Tested By**: [Name]
- **Date**: [Date]
- **Status**: ✅ PASS / ❌ FAIL
- **Notes**: [Additional comments]

---

## 📞 Escalation

If critical issues found:
1. Document issue with reproduction steps
2. Check logs for root cause
3. Consult backend team
4. Create bug ticket in issue tracker
5. Schedule fix/review

**Contact**: [Backend Team Email]

---

**Next Steps After Testing**:
1. Fix any identified issues
2. Re-run failed test cases
3. Perform regression testing
4. Deploy to staging environment
5. Production deployment

---

**Status**: Ready for Execution
**Last Updated**: January 31, 2024
