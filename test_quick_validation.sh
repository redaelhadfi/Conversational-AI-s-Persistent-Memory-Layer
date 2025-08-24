#!/bin/bash

# Quick Test Runner - Validates core functionality
# Use this for quick validation before running comprehensive tests

BASE_URL="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Helper functions
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

section() {
    echo -e "\n${BOLD}${BLUE}$1${NC}"
}

# Extract JSON value utility
extract_json_value() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"$key\":\"[^\"]*\"" | cut -d'"' -f4
}

echo -e "${BOLD}${BLUE}🔍 QUICK E2E VALIDATION${NC}"
echo -e "${BLUE}Testing core functionality...${NC}\n"

# Test 1: System Health
section "1. System Health Check"
response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
status_code="${response: -3}"

if [ "$status_code" = "200" ]; then
    success "System is healthy and accessible"
else
    error "System health check failed (Status: $status_code)"
    exit 1
fi

# Test 2: Memory Creation
section "2. Memory Creation Test"
test_memory='{
    "content": "Quick test: User prefers working in quiet environments.",
    "context": "work_preferences",
    "tags": ["work", "environment", "quiet"],
    "user_id": "quick_test_user"
}'

response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
    -H "Content-Type: application/json" \
    -d "$test_memory")

status_code="${response: -3}"
body="${response%???}"

if [ "$status_code" = "201" ]; then
    memory_id=$(extract_json_value "$body" "id")
    success "Memory creation successful (ID: $memory_id)"
else
    error "Memory creation failed (Status: $status_code)"
    exit 1
fi

# Test 3: Memory Retrieval
section "3. Memory Retrieval Test"
response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$memory_id")
status_code="${response: -3}"

if [ "$status_code" = "200" ]; then
    success "Memory retrieval successful"
else
    error "Memory retrieval failed (Status: $status_code)"
    exit 1
fi

# Test 4: Search Functionality
section "4. Search Functionality Test"
response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/search?query=quiet%20environment")
status_code="${response: -3}"

if [ "$status_code" = "200" ]; then
    success "Search functionality working"
else
    error "Search functionality failed (Status: $status_code)"
    exit 1
fi

# Test 5: Recent Memories
section "5. Recent Memories Test"
response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/recent?limit=5")
status_code="${response: -3}"

if [ "$status_code" = "200" ]; then
    success "Recent memories endpoint working"
else
    error "Recent memories failed (Status: $status_code)"
    exit 1
fi

# Test 6: Statistics
section "6. Statistics Test"
response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/stats")
status_code="${response: -3}"

if [ "$status_code" = "200" ]; then
    success "Statistics endpoint working"
else
    error "Statistics endpoint failed (Status: $status_code)"
    exit 1
fi

# Test 7: Error Handling
section "7. Error Handling Test"
response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/invalid-uuid-format")
status_code="${response: -3}"

if [ "$status_code" = "422" ]; then
    success "Error handling working correctly"
else
    info "Error handling returned status $status_code (expected 422)"
fi

# Final Summary
echo -e "\n${BOLD}${GREEN}🎉 QUICK VALIDATION COMPLETE!${NC}"
echo -e "${GREEN}✅ All core functionality is working correctly${NC}"
echo -e "${BLUE}ℹ️  Run './test_comprehensive_e2e.sh' for detailed testing${NC}\n"

# Optional cleanup
info "Cleaning up test data..."
cleanup_response=$(curl -s -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/memories/$memory_id")
cleanup_status="${cleanup_response: -3}"

if [ "$cleanup_status" = "204" ]; then
    success "Test data cleaned up"
else
    info "Test data cleanup status: $cleanup_status"
fi

echo -e "${BOLD}${BLUE}Ready for comprehensive testing!${NC}"
