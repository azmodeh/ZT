#!/bin/bash
# Zero Tolerance API - Smoke Test Suite
# تست سریع تمام endpoints

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://127.0.0.1:8088}"
TIMEOUT=10

echo -e "${CYAN}🧪 Zero Tolerance API - Smoke Test Suite${NC}"
echo -e "${CYAN}===========================================${NC}"
echo -e "API URL: $API_URL"
echo ""

passed=0
failed=0

# Test helper
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"
    
    echo -n "Testing $name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" --max-time $TIMEOUT 2>/dev/null || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --max-time $TIMEOUT 2>/dev/null || echo "000")
    fi
    
    status_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        ((passed++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        echo -e "${YELLOW}Response: $body${NC}"
        ((failed++))
        return 1
    fi
}

# Run tests
echo -e "${CYAN}1️⃣  Health Checks${NC}"
test_endpoint "/health" "GET" "/health"
test_endpoint "/ready" "GET" "/ready"
test_endpoint "/live" "GET" "/live"
echo ""

echo -e "${CYAN}2️⃣  Validation${NC}"
test_endpoint "/validate (empty)" "POST" "/validate" "{}"
echo ""

echo -e "${CYAN}3️⃣  Queue (Dry-Run)${NC}"
export ZT_DRY_RUN=1
test_endpoint "/queue (safe)" "POST" "/queue" '{"mode":"safe"}'
echo ""

echo -e "${CYAN}4️⃣  Learning${NC}"
test_endpoint "/learn" "POST" "/learn" "{}"
echo ""

# Summary
echo -e "${CYAN}===========================================${NC}"
echo -e "${GREEN}✅ Passed: $passed${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}❌ Failed: $failed${NC}"
    echo ""
    echo -e "${RED}Some tests failed. Please check the API server.${NC}"
    exit 1
else
    echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
    exit 0
fi
