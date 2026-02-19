#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   RIDER APP - COMPREHENSIVE BACKEND INTEGRATION TEST           ║${NC}"
echo -e "${BLUE}║   Date: $(date '+%B %d, %Y')                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

PASSED=0
FAILED=0

test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local expected_code=$5
    
    echo -e "\n${YELLOW}Testing:${NC} $name"
    echo -e "  Method: $method"
    echo -e "  URL: $url"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$url" -H "Content-Type: application/json")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$url" -H "Content-Type: application/json" -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    echo -e "  Response Code: ${http_code}"
    
    if [[ "$http_code" =~ $expected_code ]]; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "  ${RED}✗ FAILED${NC} (Expected: $expected_code)"
        ((FAILED++))
    fi
    
    if [ ! -z "$body" ] && [ "$body" != "null" ]; then
        echo -e "  Body: $(echo "$body" | head -c 80)..."
    fi
}

# ============================================
echo -e "\n${BLUE}═══ PHASE 1: SERVICE HEALTH CHECKS ═══${NC}"
# ============================================

test_endpoint "API Gateway Health" "GET" "http://localhost:8000/health" "" "200"
test_endpoint "Booking Service Response" "POST" "http://localhost:8100/book" '{"pickup_address":"Test","pickup_lat":5.5,"pickup_lng":-0.2,"dropoff_address":"Test2","dropoff_lat":5.6,"dropoff_lng":-0.3,"phone":"+233501234567"}' "200"

# ============================================
echo -e "\n${BLUE}═══ PHASE 2: BOOKING SERVICE TESTS ═══${NC}"
# ============================================

test_endpoint "Calculate Route (Accra to Kasoa)" "POST" "http://localhost:8100/book" \
    '{"pickup_address":"Osu, Accra","pickup_lat":5.5834,"pickup_lng":-0.1859,"dropoff_address":"Kasoa","dropoff_lat":5.6500,"dropoff_lng":-0.3000,"phone":"+233501234567"}' \
    "200"

test_endpoint "Calculate Route (Short Distance)" "POST" "http://localhost:8100/book" \
    '{"pickup_address":"A","pickup_lat":5.5,"pickup_lng":-0.2,"dropoff_address":"B","dropoff_lat":5.501,"dropoff_lng":-0.201,"phone":"+233501234567"}' \
    "200"

test_endpoint "Invalid Coordinates" "POST" "http://localhost:8100/book" \
    '{"pickup_address":"Test","pickup_lat":91,"pickup_lng":-0.2,"dropoff_address":"Test2","dropoff_lat":5.6,"dropoff_lng":-0.3,"phone":"+233501234567"}' \
    "400|422"

# ============================================
echo -e "\n${BLUE}═══ PHASE 3: DATABASE CONNECTIVITY ═══${NC}"
# ============================================

echo -e "\n${YELLOW}Testing:${NC} PostgreSQL Connection"
pg_version=$(psql -h localhost -U postgres -c "SELECT version();" 2>&1 | grep -i "PostgreSQL" | head -1)
if [ ! -z "$pg_version" ]; then
    echo -e "  ${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "  ${RED}✗ FAILED${NC} - Cannot connect to PostgreSQL"
    ((FAILED++))
fi

# ============================================
echo -e "\n${BLUE}═══ FINAL RESULTS ═══${NC}"
# ============================================

TOTAL=$((PASSED + FAILED))
PASS_RATE=$((PASSED * 100 / TOTAL))

echo -e "\n${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "Total: $TOTAL"
echo -e "Pass Rate: ${PASS_RATE}%"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "\n${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
