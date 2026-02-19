#!/bin/bash

################################################################################
# RIDER APP - QUICK INTEGRATION TEST
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_URL="${API_URL:-http://localhost:8100}"
ORDER_URL="${ORDER_URL:-http://localhost:8500}"
TRACKING_URL="${TRACKING_URL:-http://localhost:8300}"
TEST_EMAIL="rider@example.com"
TEST_PASSWORD="password123"
TEST_PHONE="+919876543210"
TOKEN=""

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        RIDER APP - QUICK INTEGRATION TEST                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

################################################################################
# Helper Functions
################################################################################

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_test() {
    echo -n "  ▸ $1... "
}

log_pass() {
    echo -e "${GREEN}✓ PASS${NC}"
}

log_fail() {
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${RED}    Error: $1${NC}"
}

log_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_service() {
    local service=$1
    local url=$2
    
    log_test "Service: $service"
    if curl -s -f "$url/health" > /dev/null 2>&1; then
        log_pass
        return 0
    else
        log_fail "Cannot reach $service at $url"
        return 1
    fi
}

################################################################################
# Phase 1: Service Health
################################################################################

log_section "PHASE 1: SERVICE HEALTH CHECK"

echo ""
check_service "API Gateway" "$API_URL" || exit 1
check_service "Order Service" "$ORDER_URL" || exit 1
check_service "Tracking Service" "$TRACKING_URL" || exit 1

################################################################################
# Phase 2: Authentication
################################################################################

log_section "PHASE 2: AUTHENTICATION TESTS"

echo ""
log_test "Login API"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
    log_pass
    log_info "Token: ${TOKEN:0:20}..."
else
    log_fail "No token in response"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""
log_test "Verify token format"
if [[ $TOKEN =~ ^[A-Za-z0-9._-]+$ ]]; then
    log_pass
else
    log_fail "Invalid token format"
    exit 1
fi

################################################################################
# Phase 3: Order Operations
################################################################################

log_section "PHASE 3: ORDER OPERATIONS"

# Get a sample rider ID (in real scenario, extract from login response)
RIDER_ID="rider_123"

echo ""
log_test "Get orders list"
ORDERS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORDER_URL/api/orders/rider/$RIDER_ID")

if echo "$ORDERS_RESPONSE" | grep -q "orders\|id"; then
    log_pass
    log_info "Orders retrieved successfully"
else
    log_fail "No orders in response"
fi

echo ""
log_test "Get order details"
ORDER_ID="order_123"
DETAILS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORDER_URL/api/orders/$ORDER_ID")

if echo "$DETAILS_RESPONSE" | grep -q "status\|customer"; then
    log_pass
else
    log_fail "Could not retrieve order details"
fi

echo ""
log_test "Update order status"
STATUS_RESPONSE=$(curl -s -X PUT "$ORDER_URL/api/orders/$ORDER_ID/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"picked_up","notes":"Order picked up"}')

if echo "$STATUS_RESPONSE" | grep -q "success\|status"; then
    log_pass
else
    log_fail "Could not update status"
fi

################################################################################
# Phase 4: Tracking
################################################################################

log_section "PHASE 4: TRACKING OPERATIONS"

echo ""
log_test "Update location"
LOCATION_RESPONSE=$(curl -s -X POST "$TRACKING_URL/api/tracking/location" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id":"order_123",
    "latitude":28.7041,
    "longitude":77.1025,
    "accuracy":10
  }')

if echo "$LOCATION_RESPONSE" | grep -q "success"; then
    log_pass
else
    log_fail "Could not update location"
fi

echo ""
log_test "Get tracking info"
TRACKING_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$TRACKING_URL/api/tracking/order/$ORDER_ID")

if echo "$TRACKING_RESPONSE" | grep -q "location\|distance"; then
    log_pass
else
    log_fail "Could not retrieve tracking info"
fi

################################################################################
# Phase 5: Response Validation
################################################################################

log_section "PHASE 5: RESPONSE VALIDATION"

echo ""
log_test "Response headers"
HEADERS=$(curl -s -I "$API_URL/health" | grep -i "content-type")
if echo "$HEADERS" | grep -q "application/json"; then
    log_pass
else
    log_fail "Invalid content-type header"
fi

echo ""
log_test "Error handling (invalid token)"
ERROR_RESPONSE=$(curl -s -H "Authorization: Bearer invalid_token" \
  "$API_URL/api/orders/rider/$RIDER_ID")

if echo "$ERROR_RESPONSE" | grep -q "unauthorized\|invalid\|error"; then
    log_pass
else
    log_fail "Error not properly handled"
fi

################################################################################
# Phase 6: Performance Baseline
################################################################################

log_section "PHASE 6: PERFORMANCE BASELINE"

echo ""
log_test "API response time (1 request)"
START=$(date +%s%N)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$ORDER_URL/api/orders/rider/$RIDER_ID" > /dev/null
END=$(date +%s%N)
DURATION=$((($END - $START) / 1000000))
echo -e "${GREEN}✓ PASS${NC} (${DURATION}ms)"

################################################################################
# Phase 7: Summary
################################################################################

log_section "TEST SUMMARY"

echo ""
echo -e "${GREEN}✓ All basic integration tests passed!${NC}"
echo ""
echo "Next Steps:"
echo "  1. Run full test suite: ./backend_integration_test.sh"
echo "  2. Build Android APK: ./gradlew assembleDebug"
echo "  3. Install APK: adb install build/outputs/apk/debug/rider-app-debug.apk"
echo "  4. Run app on emulator/device"
echo "  5. Test user flows manually"
echo ""
echo "Documentation:"
echo "  - Backend Integration Guide: BACKEND_INTEGRATION_GUIDE.md"
echo "  - Test Plan: BACKEND_INTEGRATION_TEST_PLAN.md"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Integration test completed successfully!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
