#!/bin/bash

# Conversational AI Memory System - End-to-End Test Script
# Tests all major functionality using curl commands

BASE_URL="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Helper functions
log() {
    echo -e "${BLUE}$1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Test 1: Health Check
test_health_check() {
    log "Testing health check endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        # Check if response contains required fields
        if echo "$body" | grep -q "\"status\"" && echo "$body" | grep -q "\"database\"" && echo "$body" | grep -q "\"vector_db\""; then
            success "Health check passed - System is healthy"
            info "$(echo "$body" | grep -o '\"status\":\"[^\"]*\"' | cut -d'"' -f4) system detected"
        else
            error "Health check response missing required fields"
        fi
    else
        error "Health check failed with status $status_code"
    fi
}

# Test 2: Create Memory
test_create_memory() {
    log "Testing memory creation..."
    
    local test_data='{
        "content": "E2E Test: User loves mountain hiking and prefers early morning adventures.",
        "context": "outdoor_activities",
        "tags": ["hiking", "mountains", "morning"],
        "user_id": "e2e_test_user",
        "conversation_id": "e2e_conv_001",
        "importance_score": 8
    }'
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "201" ]; then
        # Extract memory ID for later tests
        MEMORY_ID=$(echo "$body" | grep -o '\"id\":\"[^\"]*\"' | cut -d'"' -f4)
        success "Memory created successfully - ID: $MEMORY_ID"
        echo "$body" > /tmp/created_memory.json
    else
        error "Memory creation failed with status $status_code"
        info "Response: $body"
    fi
}

# Test 3: Get Memory by ID
test_get_memory() {
    if [ -z "$MEMORY_ID" ]; then
        error "No memory ID available for retrieval test"
        return
    fi
    
    log "Testing memory retrieval by ID..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$MEMORY_ID")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        if echo "$body" | grep -q "$MEMORY_ID"; then
            success "Memory retrieved successfully"
            # Check access count
            access_count=$(echo "$body" | grep -o '\"access_count\":[0-9]*' | cut -d':' -f2)
            info "Access count: $access_count"
        else
            error "Retrieved memory ID doesn't match"
        fi
    else
        error "Memory retrieval failed with status $status_code"
    fi
}

# Test 4: Recent Memories
test_recent_memories() {
    log "Testing recent memories endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/recent?limit=5")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        # Check if it's a valid JSON array with content
        if echo "$body" | grep -q '\[.*\]' && echo "$body" | grep -q '\"content\"'; then
            memory_count=$(echo "$body" | grep -o '\"id\":' | wc -l | xargs)
            success "Recent memories retrieved - Count: $memory_count"
        else
            error "Recent memories returned invalid data"
        fi
    else
        error "Recent memories failed with status $status_code"
    fi
}

# Test 5: Memory Statistics
test_memory_stats() {
    log "Testing memory statistics endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/stats")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        if echo "$body" | grep -q '\"total_memories\"' && echo "$body" | grep -q '\"total_users\"'; then
            total_memories=$(echo "$body" | grep -o '\"total_memories\":[0-9]*' | cut -d':' -f2)
            total_users=$(echo "$body" | grep -o '\"total_users\":[0-9]*' | cut -d':' -f2)
            success "Memory statistics retrieved"
            info "Total memories: $total_memories"
            info "Total users: $total_users"
        else
            error "Statistics response missing required fields"
        fi
    else
        error "Memory stats failed with status $status_code"
    fi
}

# Test 6: Search Memories
test_search_memories() {
    log "Testing memory search endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/search?query=hiking%20mountain&limit=5")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        if echo "$body" | grep -q '\"memories\"' && echo "$body" | grep -q '\"total_count\"'; then
            total_count=$(echo "$body" | grep -o '\"total_count\":[0-9]*' | cut -d':' -f2)
            search_type=$(echo "$body" | grep -o '\"search_type\":\"[^\"]*\"' | cut -d'"' -f4)
            success "Memory search completed"
            info "Found $total_count memories using $search_type search"
        else
            error "Search response missing required fields"
        fi
    else
        error "Memory search failed with status $status_code"
        info "Response: $body"
    fi
}

# Test 7: Validation Error Handling
test_validation() {
    log "Testing validation and error handling..."
    
    # Test with missing content
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d '{"context": "test"}')
    
    status_code="${response: -3}"
    
    if [ "$status_code" = "422" ]; then
        success "Validation correctly rejected missing content"
    else
        error "Validation should have failed for missing content (got $status_code)"
    fi
    
    # Test with invalid UUID
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/invalid-uuid")
    status_code="${response: -3}"
    
    if [ "$status_code" = "422" ]; then
        success "Validation correctly rejected invalid UUID"
    else
        error "Validation should have failed for invalid UUID (got $status_code)"
    fi
}

# Test 8: Create Additional Test Data
test_create_multiple_memories() {
    log "Creating multiple test memories..."
    
    local memories=(
        '{"content": "User enjoys Italian cuisine, especially carbonara pasta.", "context": "food_preferences", "tags": ["food", "italian"], "user_id": "e2e_test_user"}'
        '{"content": "User works as a software engineer at a startup.", "context": "professional", "tags": ["career", "tech"], "user_id": "e2e_test_user"}'
        '{"content": "User is planning a trip to Japan in spring.", "context": "travel", "tags": ["travel", "japan"], "user_id": "e2e_test_user"}'
    )
    
    local created=0
    for memory in "${memories[@]}"; do
        response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
            -H "Content-Type: application/json" \
            -d "$memory")
        
        status_code="${response: -3}"
        
        if [ "$status_code" = "201" ]; then
            ((created++))
        fi
    done
    
    if [ $created -eq ${#memories[@]} ]; then
        success "Created $created additional test memories"
    else
        error "Only created $created out of ${#memories[@]} memories"
    fi
}

# Main test execution
main() {
    echo -e "${BOLD}🚀 Starting Comprehensive End-to-End Testing${NC}"
    echo -e "${BLUE}Testing against: $BASE_URL${NC}"
    echo "============================================================"
    
    # Run all tests
    test_health_check
    sleep 1
    
    test_create_memory
    sleep 1
    
    test_get_memory
    sleep 1
    
    test_recent_memories
    sleep 1
    
    test_memory_stats
    sleep 1
    
    test_create_multiple_memories
    sleep 2
    
    test_search_memories
    sleep 1
    
    test_validation
    
    # Print summary
    echo "============================================================"
    local total=$((PASSED + FAILED))
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}${BOLD}🎉 ALL TESTS PASSED! ($PASSED/$total)${NC}"
        echo -e "${GREEN}✅ Conversational AI Memory System is fully functional!${NC}"
    else
        echo -e "${YELLOW}${BOLD}⚠️  TEST RESULTS: $PASSED passed, $FAILED failed ($total total)${NC}"
    fi
    
    echo "============================================================"
    
    # Clean up
    rm -f /tmp/created_memory.json
    
    # Exit with appropriate code
    if [ $FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run the main function
main
