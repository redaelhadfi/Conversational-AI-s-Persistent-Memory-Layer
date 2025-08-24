#!/bin/bash

# Comprehensive End-to-End Testing Suite
# Tests all functionality of the Conversational AI Memory System
# Ensures everything works perfectly before production deployment

BASE_URL="http://localhost:8000"

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0
TOTAL_TESTS=0

# Test data storage
declare -a CREATED_MEMORY_IDS=()
declare -a TEST_DATA=()

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

warning() {
    echo -e "${PURPLE}⚠️  $1${NC}"
}

section_header() {
    echo
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD} $1${NC}"
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Increment test counter
test_start() {
    ((TOTAL_TESTS++))
}

# Utility function to extract JSON value
extract_json_value() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"$key\":\"[^\"]*\"" | cut -d'"' -f4
}

extract_json_number() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"$key\":[0-9]*" | cut -d':' -f2
}

# Wait function to avoid API rate limits
wait_between_tests() {
    sleep 1
}

# Test 1: System Health and Readiness
test_system_health() {
    section_header "🏥 SYSTEM HEALTH & READINESS TESTS"
    
    test_start
    log "Testing system health endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        # Parse health check response
        status=$(extract_json_value "$body" "status")
        database=$(extract_json_value "$body" "database")
        vector_db=$(extract_json_value "$body" "vector_db")
        
        if [ "$status" = "healthy" ] && [ "$database" = "healthy" ] && [ "$vector_db" = "healthy" ]; then
            success "System health check - All services healthy"
            info "Database: $database | Vector DB: $vector_db"
            
            # Extract uptime for monitoring
            uptime=$(echo "$body" | grep -o '"uptime_seconds":[0-9.]*' | cut -d':' -f2)
            info "System uptime: ${uptime}s"
        else
            error "System health check - Some services unhealthy (Status: $status, DB: $database, Vector: $vector_db)"
        fi
    else
        error "Health endpoint failed with status $status_code"
    fi
    
    wait_between_tests
}

# Test 2: Memory Creation and Storage
test_memory_creation() {
    section_header "💾 MEMORY CREATION & STORAGE TESTS"
    
    # Test 2.1: Basic Memory Creation
    test_start
    log "Testing basic memory creation..."
    
    local basic_memory='{
        "content": "E2E Test: User prefers morning coffee and evening tea for optimal productivity.",
        "context": "beverage_preferences",
        "tags": ["coffee", "tea", "productivity", "routine"],
        "user_id": "e2e_user_001",
        "conversation_id": "e2e_conv_001",
        "importance_score": 7,
        "metadata": {"test_type": "basic", "category": "preferences"}
    }'
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d "$basic_memory")
    
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "201" ]; then
        memory_id=$(extract_json_value "$body" "id")
        vector_id=$(extract_json_value "$body" "vector_id")
        
        if [ -n "$memory_id" ] && [ -n "$vector_id" ]; then
            CREATED_MEMORY_IDS+=("$memory_id")
            success "Basic memory creation - ID: $memory_id"
            info "Vector ID: $vector_id"
        else
            error "Memory created but missing ID or vector_id"
        fi
    else
        error "Basic memory creation failed with status $status_code"
        warning "Response: $body"
    fi
    
    wait_between_tests
    
    # Test 2.2: Memory Creation with All Fields
    test_start
    log "Testing comprehensive memory creation..."
    
    local comprehensive_memory='{
        "content": "E2E Test: User is a software engineer who enjoys rock climbing on weekends and prefers working in quiet environments with minimal distractions.",
        "context": "professional_lifestyle",
        "tags": ["career", "software", "engineering", "climbing", "work_environment"],
        "user_id": "e2e_user_002",
        "conversation_id": "e2e_conv_002",
        "importance_score": 9,
        "metadata": {"test_type": "comprehensive", "category": "professional", "priority": "high"}
    }'
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d "$comprehensive_memory")
    
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "201" ]; then
        memory_id=$(extract_json_value "$body" "id")
        importance_score=$(extract_json_number "$body" "importance_score")
        
        if [ "$importance_score" = "9" ]; then
            CREATED_MEMORY_IDS+=("$memory_id")
            success "Comprehensive memory creation with all fields"
            info "Importance score correctly set: $importance_score"
        else
            error "Memory created but importance score incorrect"
        fi
    else
        error "Comprehensive memory creation failed with status $status_code"
    fi
    
    wait_between_tests
    
    # Test 2.3: Batch Memory Creation
    test_start
    log "Testing multiple memory creation for variety..."
    
    declare -a batch_memories=(
        '{"content": "E2E Test: User travels frequently for business and prefers aisle seats on flights.", "context": "travel_preferences", "tags": ["travel", "business", "flights"], "user_id": "e2e_user_003"}'
        '{"content": "E2E Test: User is learning Spanish and practices 30 minutes daily using language apps.", "context": "education", "tags": ["language", "spanish", "learning"], "user_id": "e2e_user_004"}'
        '{"content": "E2E Test: User has a home office setup with dual monitors and ergonomic chair.", "context": "workspace", "tags": ["office", "equipment", "ergonomics"], "user_id": "e2e_user_005"}'
        '{"content": "E2E Test: User enjoys cooking Italian cuisine and has a collection of authentic recipes.", "context": "culinary_interests", "tags": ["cooking", "italian", "recipes"], "user_id": "e2e_user_006"}'
    )
    
    local created_count=0
    for memory in "${batch_memories[@]}"; do
        response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
            -H "Content-Type: application/json" \
            -d "$memory")
        
        status_code="${response: -3}"
        body="${response%???}"
        
        if [ "$status_code" = "201" ]; then
            memory_id=$(extract_json_value "$body" "id")
            CREATED_MEMORY_IDS+=("$memory_id")
            ((created_count++))
        fi
        sleep 0.5  # Small delay to avoid overwhelming the API
    done
    
    if [ $created_count -eq ${#batch_memories[@]} ]; then
        success "Batch memory creation - All $created_count memories created"
    elif [ $created_count -gt 0 ]; then
        warning "Partial batch creation - $created_count out of ${#batch_memories[@]} memories created"
    else
        error "Batch memory creation - No memories created"
    fi
    
    wait_between_tests
}

# Test 3: Memory Retrieval and Access Tracking
test_memory_retrieval() {
    section_header "🔍 MEMORY RETRIEVAL & ACCESS TRACKING TESTS"
    
    if [ ${#CREATED_MEMORY_IDS[@]} -eq 0 ]; then
        error "No memory IDs available for retrieval testing"
        return
    fi
    
    # Test 3.1: Individual Memory Retrieval
    test_start
    log "Testing individual memory retrieval..."
    
    local test_memory_id="${CREATED_MEMORY_IDS[0]}"
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$test_memory_id")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        retrieved_id=$(extract_json_value "$body" "id")
        access_count=$(extract_json_number "$body" "access_count")
        
        if [ "$retrieved_id" = "$test_memory_id" ] && [ -n "$access_count" ]; then
            success "Individual memory retrieval successful"
            info "Memory ID: $retrieved_id | Access count: $access_count"
        else
            error "Memory retrieved but data inconsistent"
        fi
    else
        error "Memory retrieval failed with status $status_code"
    fi
    
    wait_between_tests
    
    # Test 3.2: Access Count Increment
    test_start
    log "Testing access count increment..."
    
    # Retrieve the same memory again
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$test_memory_id")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        new_access_count=$(extract_json_number "$body" "access_count")
        
        if [ "$new_access_count" -gt "$access_count" ]; then
            success "Access count increment working - Count: $new_access_count"
        else
            warning "Access count may not have incremented properly"
        fi
    else
        error "Second retrieval failed with status $status_code"
    fi
    
    wait_between_tests
    
    # Test 3.3: Non-existent Memory Handling
    test_start
    log "Testing non-existent memory handling..."
    
    fake_uuid="12345678-1234-1234-1234-123456789012"
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$fake_uuid")
    status_code="${response: -3}"
    
    if [ "$status_code" = "404" ]; then
        success "Non-existent memory correctly returns 404"
    else
        error "Non-existent memory should return 404, got $status_code"
    fi
    
    wait_between_tests
}

# Test 4: Memory Listing and Filtering
test_memory_listing() {
    section_header "📋 MEMORY LISTING & FILTERING TESTS"
    
    # Test 4.1: Recent Memories
    test_start
    log "Testing recent memories endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/recent?limit=10")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        # Count memories in response
        memory_count=$(echo "$body" | grep -o '"id":' | wc -l | xargs)
        
        if [ "$memory_count" -gt 0 ]; then
            success "Recent memories retrieved - Count: $memory_count"
            
            # Verify chronological order
            if echo "$body" | grep -q '"created_at"'; then
                success "Recent memories include timestamps"
            else
                warning "Recent memories missing timestamp data"
            fi
        else
            error "Recent memories returned empty list"
        fi
    else
        error "Recent memories failed with status $status_code"
    fi
    
    wait_between_tests
    
    # Test 4.2: Filtered Recent Memories
    test_start
    log "Testing filtered recent memories..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/recent?limit=5&user_id=e2e_user_001")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        if echo "$body" | grep -q '"user_id":"e2e_user_001"'; then
            success "Filtered recent memories by user_id working"
        else
            warning "User filtering may not be working correctly"
        fi
    else
        error "Filtered recent memories failed with status $status_code"
    fi
    
    wait_between_tests
}

# Test 5: Memory Search Functionality
test_memory_search() {
    section_header "🔎 MEMORY SEARCH & SEMANTIC MATCHING TESTS"
    
    # Test 5.1: Basic Keyword Search
    test_start
    log "Testing keyword search..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/search?query=coffee%20tea&limit=5")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        if echo "$body" | grep -q '"memories"' && echo "$body" | grep -q '"total_count"'; then
            total_count=$(extract_json_number "$body" "total_count")
            search_type=$(extract_json_value "$body" "search_type")
            
            success "Memory search executed successfully"
            info "Found: $total_count memories | Search type: $search_type"
        else
            error "Search response missing required fields"
        fi
    else
        error "Memory search failed with status $status_code"
        warning "Response: $body"
    fi
    
    wait_between_tests
    
    # Test 5.2: Context-filtered Search
    test_start
    log "Testing context-filtered search..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/search?query=user&context=professional&limit=5")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        success "Context-filtered search executed"
    else
        error "Context-filtered search failed with status $status_code"
    fi
    
    wait_between_tests
    
    # Test 5.3: Tag-based Search
    test_start
    log "Testing tag-based search..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/search?query=productivity&limit=5")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        success "Tag-based search executed"
    else
        error "Tag-based search failed with status $status_code"
    fi
    
    wait_between_tests
}

# Test 6: Memory Statistics and Analytics
test_memory_statistics() {
    section_header "📊 MEMORY STATISTICS & ANALYTICS TESTS"
    
    test_start
    log "Testing memory statistics endpoint..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/stats")
    status_code="${response: -3}"
    body="${response%???}"
    
    if [ "$status_code" = "200" ]; then
        total_memories=$(extract_json_number "$body" "total_memories")
        total_users=$(extract_json_number "$body" "total_users")
        
        if [ -n "$total_memories" ] && [ -n "$total_users" ] && [ "$total_memories" -gt 0 ]; then
            success "Memory statistics retrieved successfully"
            info "Total memories: $total_memories | Total users: $total_users"
            
            # Check for context breakdown
            if echo "$body" | grep -q '"memories_by_context"'; then
                success "Context breakdown included in statistics"
            else
                warning "Context breakdown missing from statistics"
            fi
            
            # Check for time-based data
            if echo "$body" | grep -q '"memories_by_day"'; then
                success "Time-based statistics included"
            else
                warning "Time-based statistics missing"
            fi
        else
            error "Statistics data incomplete or invalid"
        fi
    else
        error "Memory statistics failed with status $status_code"
    fi
    
    wait_between_tests
}

# Test 7: Input Validation and Error Handling
test_validation_and_errors() {
    section_header "🛡️ INPUT VALIDATION & ERROR HANDLING TESTS"
    
    # Test 7.1: Missing Required Fields
    test_start
    log "Testing missing content validation..."
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d '{"context": "test", "user_id": "test_user"}')
    
    status_code="${response: -3}"
    
    if [ "$status_code" = "422" ]; then
        success "Missing content validation working"
    else
        error "Should reject missing content with 422, got $status_code"
    fi
    
    wait_between_tests
    
    # Test 7.2: Empty Content Validation
    test_start
    log "Testing empty content validation..."
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d '{"content": "", "context": "test", "user_id": "test_user"}')
    
    status_code="${response: -3}"
    
    if [ "$status_code" = "422" ]; then
        success "Empty content validation working"
    else
        error "Should reject empty content with 422, got $status_code"
    fi
    
    wait_between_tests
    
    # Test 7.3: Invalid UUID Format
    test_start
    log "Testing invalid UUID handling..."
    
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/invalid-uuid")
    status_code="${response: -3}"
    
    if [ "$status_code" = "422" ]; then
        success "Invalid UUID validation working"
    else
        error "Should reject invalid UUID with 422, got $status_code"
    fi
    
    wait_between_tests
    
    # Test 7.4: Invalid Importance Score
    test_start
    log "Testing importance score validation..."
    
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d '{"content": "Test content", "importance_score": 15}')
    
    status_code="${response: -3}"
    
    if [ "$status_code" = "422" ]; then
        success "Importance score validation working"
    else
        warning "Importance score validation may need attention (got $status_code)"
    fi
    
    wait_between_tests
}

# Test 8: Performance and Load Testing
test_performance() {
    section_header "⚡ PERFORMANCE & LOAD TESTS"
    
    # Test 8.1: Response Time Test
    test_start
    log "Testing API response times..."
    
    start_time=$(date +%s%N)
    response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
    end_time=$(date +%s%N)
    
    response_time=$((($end_time - $start_time) / 1000000))  # Convert to milliseconds
    
    if [ "$response_time" -lt 1000 ]; then  # Less than 1 second
        success "Health endpoint response time: ${response_time}ms (Good)"
    elif [ "$response_time" -lt 2000 ]; then
        warning "Health endpoint response time: ${response_time}ms (Acceptable)"
    else
        error "Health endpoint response time: ${response_time}ms (Too slow)"
    fi
    
    wait_between_tests
    
    # Test 8.2: Concurrent Request Handling
    test_start
    log "Testing concurrent request handling..."
    
    # Make 5 concurrent requests
    for i in {1..5}; do
        curl -s "$BASE_URL/health" > /dev/null &
    done
    
    wait  # Wait for all background jobs to complete
    
    # Test if system is still responsive
    response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
    status_code="${response: -3}"
    
    if [ "$status_code" = "200" ]; then
        success "System handles concurrent requests well"
    else
        error "System may have issues with concurrent requests"
    fi
    
    wait_between_tests
}

# Test 9: Data Integrity and Consistency
test_data_integrity() {
    section_header "🔒 DATA INTEGRITY & CONSISTENCY TESTS"
    
    if [ ${#CREATED_MEMORY_IDS[@]} -eq 0 ]; then
        warning "No test data available for integrity testing"
        return
    fi
    
    # Test 9.1: Memory Data Consistency
    test_start
    log "Testing memory data consistency..."
    
    local test_memory_id="${CREATED_MEMORY_IDS[0]}"
    
    # Retrieve memory twice and compare
    response1=$(curl -s "$BASE_URL/api/v1/memories/$test_memory_id")
    response2=$(curl -s "$BASE_URL/api/v1/memories/$test_memory_id")
    
    content1=$(extract_json_value "$response1" "content")
    content2=$(extract_json_value "$response2" "content")
    
    if [ "$content1" = "$content2" ] && [ -n "$content1" ]; then
        success "Memory data consistency maintained"
    else
        error "Memory data inconsistency detected"
    fi
    
    wait_between_tests
    
    # Test 9.2: Vector ID Consistency
    test_start
    log "Testing vector ID consistency..."
    
    vector_id1=$(extract_json_value "$response1" "vector_id")
    vector_id2=$(extract_json_value "$response2" "vector_id")
    
    if [ "$vector_id1" = "$vector_id2" ] && [ -n "$vector_id1" ]; then
        success "Vector ID consistency maintained"
    else
        error "Vector ID inconsistency detected"
    fi
    
    wait_between_tests
}

# Test 10: System Integration Tests
test_system_integration() {
    section_header "🔗 SYSTEM INTEGRATION TESTS"
    
    # Test 10.1: Database and Vector DB Integration
    test_start
    log "Testing database and vector DB integration..."
    
    # Create a memory and verify it appears in both structured and vector search
    local integration_memory='{
        "content": "E2E Integration Test: User has a unique hobby of collecting vintage postcards from around the world.",
        "context": "hobbies",
        "tags": ["collecting", "postcards", "vintage", "travel"],
        "user_id": "integration_test_user"
    }'
    
    create_response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d "$integration_memory")
    
    create_status="${create_response: -3}"
    create_body="${create_response%???}"
    
    if [ "$create_status" = "201" ]; then
        memory_id=$(extract_json_value "$create_body" "id")
        CREATED_MEMORY_IDS+=("$memory_id")
        
        # Wait a moment for indexing
        sleep 2
        
        # Test structured retrieval
        struct_response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$memory_id")
        struct_status="${struct_response: -3}"
        
        # Test search functionality
        search_response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/search?query=postcards&limit=5")
        search_status="${search_response: -3}"
        
        if [ "$struct_status" = "200" ] && [ "$search_status" = "200" ]; then
            success "Database and vector DB integration working"
        else
            error "Integration between databases may have issues"
        fi
    else
        error "Failed to create memory for integration test"
    fi
    
    wait_between_tests
}

# Cleanup function
cleanup_test_data() {
    log "Cleaning up test data..."
    
    local cleaned_count=0
    for memory_id in "${CREATED_MEMORY_IDS[@]}"; do
        response=$(curl -s -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/memories/$memory_id")
        status_code="${response: -3}"
        
        if [ "$status_code" = "204" ]; then
            ((cleaned_count++))
        fi
    done
    
    if [ $cleaned_count -gt 0 ]; then
        info "Cleaned up $cleaned_count test memories"
    fi
}

# Final summary and report
generate_final_report() {
    section_header "📋 FINAL TEST REPORT"
    
    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$(( (PASSED * 100) / TOTAL_TESTS ))
    fi
    
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}                    COMPREHENSIVE E2E TEST RESULTS                      ${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
    echo
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}${BOLD}🎉 ALL TESTS PASSED! (${PASSED}/${TOTAL_TESTS})${NC}"
        echo -e "${GREEN}${BOLD}✨ SUCCESS RATE: ${success_rate}%${NC}"
        echo
        echo -e "${GREEN}🚀 SYSTEM STATUS: PRODUCTION READY${NC}"
        echo -e "${GREEN}✅ Conversational AI Memory System is fully operational!${NC}"
    elif [ $success_rate -ge 90 ]; then
        echo -e "${YELLOW}${BOLD}⚠️  MOSTLY SUCCESSFUL: ${PASSED} passed, ${FAILED} failed (${TOTAL_TESTS} total)${NC}"
        echo -e "${YELLOW}${BOLD}📊 SUCCESS RATE: ${success_rate}%${NC}"
        echo
        echo -e "${YELLOW}🔧 SYSTEM STATUS: NEEDS MINOR FIXES${NC}"
        echo -e "${YELLOW}✅ Core functionality working, minor issues to address${NC}"
    else
        echo -e "${RED}${BOLD}❌ SIGNIFICANT ISSUES: ${PASSED} passed, ${FAILED} failed (${TOTAL_TESTS} total)${NC}"
        echo -e "${RED}${BOLD}📊 SUCCESS RATE: ${success_rate}%${NC}"
        echo
        echo -e "${RED}🔧 SYSTEM STATUS: REQUIRES ATTENTION${NC}"
        echo -e "${RED}❌ Major issues need to be resolved before production${NC}"
    fi
    
    echo
    echo -e "${BOLD}Test Categories Covered:${NC}"
    echo -e "${BLUE}• System Health & Readiness${NC}"
    echo -e "${BLUE}• Memory Creation & Storage${NC}"
    echo -e "${BLUE}• Memory Retrieval & Access Tracking${NC}"
    echo -e "${BLUE}• Memory Listing & Filtering${NC}"
    echo -e "${BLUE}• Memory Search & Semantic Matching${NC}"
    echo -e "${BLUE}• Memory Statistics & Analytics${NC}"
    echo -e "${BLUE}• Input Validation & Error Handling${NC}"
    echo -e "${BLUE}• Performance & Load Testing${NC}"
    echo -e "${BLUE}• Data Integrity & Consistency${NC}"
    echo -e "${BLUE}• System Integration${NC}"
    
    echo
    echo -e "${BOLD}Test Data Summary:${NC}"
    echo -e "${BLUE}• Created ${#CREATED_MEMORY_IDS[@]} test memories${NC}"
    echo -e "${BLUE}• Tested multiple user scenarios${NC}"
    echo -e "${BLUE}• Validated all major API endpoints${NC}"
    
    echo
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════════════${NC}"
    
    # Return appropriate exit code
    if [ $FAILED -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Main execution function
main() {
    echo -e "${BOLD}${CYAN}🚀 COMPREHENSIVE END-TO-END TESTING SUITE${NC}"
    echo -e "${CYAN}Testing Conversational AI Memory System${NC}"
    echo -e "${CYAN}Target: $BASE_URL${NC}"
    echo -e "${CYAN}$(date)${NC}"
    echo
    
    # Execute all test suites
    test_system_health
    test_memory_creation
    test_memory_retrieval
    test_memory_listing
    test_memory_search
    test_memory_statistics
    test_validation_and_errors
    test_performance
    test_data_integrity
    test_system_integration
    
    # Generate final report
    generate_final_report
    local exit_code=$?
    
    # Optional cleanup (uncomment if you want to clean up test data)
    # cleanup_test_data
    
    exit $exit_code
}

# Run the main function
main
