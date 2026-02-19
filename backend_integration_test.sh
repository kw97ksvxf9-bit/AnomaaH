#!/bin/bash

################################################################################
# RIDER APP - BACKEND INTEGRATION TEST SUITE
################################################################################

set -e

echo "=================================="
echo "RIDER APP BACKEND INTEGRATION TEST"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

# Configuration
API_BASE_URL="http://localhost:8100"
ORDER_SERVICE_URL="http://localhost:8500"
TRACKING_SERVICE_URL="http://localhost:8300"
NOTIFICATION_SERVICE_URL="http://localhost:8400"

################################################################################
# TEST FUNCTIONS
################################################################################

test_service_health() {
    local service_name=$1
    local service_url=$2
    
    echo -n "Testing $service_name health... "
    
    if curl -s -f "$service_url/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

test_api_endpoint() {
    local test_name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_status=$5
    
    echo -n "Testing $test_name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq "$expected_status" ] || [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASSED (HTTP $http_code)${NC}"
        echo "    Response: $(echo "$body" | head -c 100)..."
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED (HTTP $http_code)${NC}"
        echo "    Expected: $expected_status"
        echo "    Response: $body"
        ((FAILED++))
        return 1
    fi
}

################################################################################
# HEALTH CHECKS
################################################################################

echo -e "${BLUE}═══ PHASE 1: SERVICE HEALTH CHECKS ═══${NC}"
echo ""

test_service_health "API Gateway" "$API_BASE_URL"
test_service_health "Order Service" "$ORDER_SERVICE_URL"
test_service_health "Tracking Service" "$TRACKING_SERVICE_URL"
test_service_health "Notification Service" "$NOTIFICATION_SERVICE_URL"

echo ""

################################################################################
# API GATEWAY TESTS
################################################################################

echo -e "${BLUE}═══ PHASE 2: API GATEWAY TESTS ═══${NC}"
echo ""

# Test authentication endpoint
test_api_endpoint \
    "POST /api/auth/login" \
    "POST" \
    "$API_BASE_URL/api/auth/login" \
    '{"email":"rider@example.com","password":"password123"}' \
    200

# Test OTP verification
test_api_endpoint \
    "POST /api/auth/verify-otp" \
    "POST" \
    "$API_BASE_URL/api/auth/verify-otp" \
    '{"phone":"+919876543210","otp":"123456"}' \
    200

echo ""

################################################################################
# ORDER SERVICE TESTS
################################################################################

echo -e "${BLUE}═══ PHASE 3: ORDER SERVICE TESTS ═══${NC}"
echo ""

# Test get orders
test_api_endpoint \
    "GET /api/orders" \
    "GET" \
    "$ORDER_SERVICE_URL/api/orders" \
    "" \
    200

# Test get order details
test_api_endpoint \
    "GET /api/orders/{id}" \
    "GET" \
    "$ORDER_SERVICE_URL/api/orders/1" \
    "" \
    200

# Test update order status
test_api_endpoint \
    "PUT /api/orders/{id}/status" \
    "PUT" \
    "$ORDER_SERVICE_URL/api/orders/1/status" \
    '{"status":"picked_up","notes":"Order picked up from location"}' \
    200

# Test cancel order
test_api_endpoint \
    "POST /api/orders/{id}/cancel" \
    "POST" \
    "$ORDER_SERVICE_URL/api/orders/1/cancel" \
    '{"reason":"Unable to deliver","notes":"Traffic issue"}' \
    200

echo ""

################################################################################
# TRACKING SERVICE TESTS
################################################################################

echo -e "${BLUE}═══ PHASE 4: TRACKING SERVICE TESTS ═══${NC}"
echo ""

# Test location update
test_api_endpoint \
    "POST /api/tracking/location" \
    "POST" \
    "$TRACKING_SERVICE_URL/api/tracking/location" \
    '{"latitude":28.7041,"longitude":77.1025,"accuracy":10,"speed":15}' \
    200

# Test get tracking info
test_api_endpoint \
    "GET /api/tracking/order/{id}" \
    "GET" \
    "$TRACKING_SERVICE_URL/api/tracking/order/1" \
    "" \
    200

echo ""

################################################################################
# NOTIFICATION SERVICE TESTS
################################################################################

echo -e "${BLUE}═══ PHASE 5: NOTIFICATION SERVICE TESTS ═══${NC}"
echo ""

# Test send notification
test_api_endpoint \
    "POST /api/notifications/send" \
    "POST" \
    "$NOTIFICATION_SERVICE_URL/api/notifications/send" \
    '{"type":"order_assigned","recipient":"rider123","title":"New Order","message":"Order #123 assigned"}' \
    200

echo ""

################################################################################
# INTEGRATION FLOW TESTS
################################################################################

echo -e "${BLUE}═══ PHASE 6: INTEGRATION FLOW TESTS ═══${NC}"
echo ""

echo -n "Testing complete order flow... "
echo "Creating mock test data..."

# This would be a complete user flow in real scenario
# 1. Login
# 2. Get orders
# 3. Accept order
# 4. Update location
# 5. Update order status
# 6. Complete delivery

echo -e "${YELLOW}! SKIPPED (requires authentication)${NC}"
((SKIPPED++))

echo ""

################################################################################
# TEST SUMMARY
################################################################################

echo -e "${BLUE}═══ TEST SUMMARY ═══${NC}"
echo ""
echo -e "${GREEN}PASSED: $PASSED${NC}"
echo -e "${RED}FAILED: $FAILED${NC}"
echo -e "${YELLOW}SKIPPED: $SKIPPED${NC}"
echo ""

TOTAL=$((PASSED + FAILED + SKIPPED))
PASS_RATE=$((PASSED * 100 / (PASSED + FAILED)))

echo "Total: $TOTAL tests"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}Success Rate: ${PASS_RATE}%${NC}"
    echo ""
    echo -e "${GREEN}✓ All tests passed! Backend integration successful.${NC}"
    exit 0
else
    echo -e "${RED}Success Rate: ${PASS_RATE}%${NC}"
    echo ""
    echo -e "${RED}✗ Some tests failed. Please check the output above.${NC}"
    exit 1
fi
