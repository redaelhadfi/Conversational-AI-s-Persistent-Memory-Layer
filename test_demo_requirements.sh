#!/bin/bash

# Demo Requirements Verification Test
# Tests: Working API + demo (3 saved entries, recall verified)
# Performance: <500ms recall latency, ≥90% recall accuracy

BASE_URL="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Test data
declare -a DEMO_ENTRIES=()
declare -a RECALL_TIMES=()
declare -a RECALL_RESULTS=()

echo -e "${BOLD}${BLUE}🎯 DEMO REQUIREMENTS VERIFICATION${NC}"
echo -e "${BLUE}Testing: Working API + 3 saved entries + recall verification${NC}"
echo -e "${BLUE}Performance targets: <500ms latency, ≥90% accuracy${NC}"
echo

# Helper functions
log() { echo -e "${BLUE}$1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
metric() { echo -e "${PURPLE}📊 $1${NC}"; }

extract_json_value() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"$key\":\"[^\"]*\"" | cut -d'"' -f4
}

# Step 1: Create 3 Demo Entries
echo -e "${BOLD}${GREEN}STEP 1: Creating 3 Demo Entries${NC}"

demo_memories=(
    '{"content": "User prefers morning coffee (espresso) and works best between 9-11 AM with minimal distractions.", "context": "work_preferences", "tags": ["coffee", "productivity", "morning", "focus"], "user_id": "demo_user_001", "importance_score": 8}'
    '{"content": "User enjoys weekend hiking in national parks, particularly trail running on moderate difficulty paths.", "context": "recreation", "tags": ["hiking", "outdoors", "running", "weekends"], "user_id": "demo_user_001", "importance_score": 7}'
    '{"content": "User is learning Python programming and prefers hands-on coding exercises over theoretical lectures.", "context": "learning", "tags": ["python", "programming", "learning", "coding"], "user_id": "demo_user_001", "importance_score": 9}'
)

echo
for i in "${!demo_memories[@]}"; do
    entry_num=$((i + 1))
    log "Creating demo entry $entry_num/3..."
    
    start_time=$(date +%s%N)
    response=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/memories" \
        -H "Content-Type: application/json" \
        -d "${demo_memories[$i]}")
    end_time=$(date +%s%N)
    
    status_code="${response: -3}"
    body="${response%???}"
    creation_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ "$status_code" = "201" ]; then
        memory_id=$(extract_json_value "$body" "id")
        DEMO_ENTRIES+=("$memory_id")
        success "Demo entry $entry_num created successfully (${creation_time}ms)"
        info "ID: $memory_id"
    else
        error "Demo entry $entry_num failed (Status: $status_code)"
        echo "Response: $body"
    fi
    echo
done

echo -e "${BOLD}${GREEN}✅ Demo entries created: ${#DEMO_ENTRIES[@]}/3${NC}"
echo

# Step 2: Verify All Entries Are Saved
echo -e "${BOLD}${GREEN}STEP 2: Verifying Saved Entries${NC}"
echo

for i in "${!DEMO_ENTRIES[@]}"; do
    entry_num=$((i + 1))
    memory_id="${DEMO_ENTRIES[$i]}"
    
    log "Verifying demo entry $entry_num..."
    
    start_time=$(date +%s%N)
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$memory_id")
    end_time=$(date +%s%N)
    
    status_code="${response: -3}"
    body="${response%???}"
    retrieval_time=$(( (end_time - start_time) / 1000000 ))
    
    RECALL_TIMES+=($retrieval_time)
    
    if [ "$status_code" = "200" ]; then
        content=$(extract_json_value "$body" "content")
        user_id=$(extract_json_value "$body" "user_id")
        
        if [ "$user_id" = "demo_user_001" ] && [ -n "$content" ]; then
            RECALL_RESULTS+=("SUCCESS")
            success "Entry $entry_num recalled successfully (${retrieval_time}ms)"
            info "Content preview: ${content:0:60}..."
            
            # Performance check
            if [ $retrieval_time -lt 500 ]; then
                metric "✅ Latency: ${retrieval_time}ms < 500ms target"
            else
                metric "⚠️  Latency: ${retrieval_time}ms > 500ms target"
            fi
        else
            RECALL_RESULTS+=("FAILED")
            error "Entry $entry_num data integrity issue"
        fi
    else
        RECALL_RESULTS+=("FAILED")
        error "Entry $entry_num recall failed (Status: $status_code)"
    fi
    echo
done

# Step 3: Test Semantic Recall Accuracy
echo -e "${BOLD}${GREEN}STEP 3: Testing Semantic Recall Accuracy${NC}"
echo

# Test queries that should match our demo entries
test_queries=(
    "coffee morning productivity"
    "hiking outdoors weekend"
    "python programming learning"
)

expected_matches=3
actual_matches=0

for i in "${!test_queries[@]}"; do
    query="${test_queries[$i]}"
    entry_num=$((i + 1))
    
    log "Testing semantic recall: \"$query\"..."
    
    start_time=$(date +%s%N)
    response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/search?query=$(echo "$query" | sed 's/ /%20/g')&limit=5&user_id=demo_user_001")
    end_time=$(date +%s%N)
    
    status_code="${response: -3}"
    body="${response%???}"
    search_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ "$status_code" = "200" ]; then
        # Count memories returned
        memory_count=$(echo "$body" | grep -o '"id":' | wc -l | xargs)
        
        if [ "$memory_count" -gt 0 ]; then
            ((actual_matches++))
            success "Query $entry_num found $memory_count relevant memories (${search_time}ms)"
        else
            error "Query $entry_num found no matches (${search_time}ms)"
        fi
        
        # Performance check
        if [ $search_time -lt 500 ]; then
            metric "✅ Search latency: ${search_time}ms < 500ms target"
        else
            metric "⚠️  Search latency: ${search_time}ms > 500ms target"
        fi
    else
        error "Query $entry_num failed (Status: $status_code)"
    fi
    echo
done

# Step 4: Calculate Performance Metrics
echo -e "${BOLD}${GREEN}STEP 4: Performance Analysis${NC}"
echo

# Calculate average recall latency
total_time=0
for time in "${RECALL_TIMES[@]}"; do
    total_time=$((total_time + time))
done

if [ ${#RECALL_TIMES[@]} -gt 0 ]; then
    avg_latency=$((total_time / ${#RECALL_TIMES[@]}))
else
    avg_latency=0
fi

# Calculate recall accuracy
successful_recalls=0
for result in "${RECALL_RESULTS[@]}"; do
    if [ "$result" = "SUCCESS" ]; then
        ((successful_recalls++))
    fi
done

if [ ${#RECALL_RESULTS[@]} -gt 0 ]; then
    recall_accuracy=$((successful_recalls * 100 / ${#RECALL_RESULTS[@]}))
else
    recall_accuracy=0
fi

# Calculate semantic accuracy
if [ $expected_matches -gt 0 ]; then
    semantic_accuracy=$((actual_matches * 100 / expected_matches))
else
    semantic_accuracy=0
fi

echo -e "${BOLD}📊 PERFORMANCE METRICS${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Individual recall times
echo -e "${BOLD}Individual Recall Times:${NC}"
for i in "${!RECALL_TIMES[@]}"; do
    entry_num=$((i + 1))
    time="${RECALL_TIMES[$i]}"
    if [ $time -lt 500 ]; then
        echo -e "${GREEN}  Entry $entry_num: ${time}ms ✅${NC}"
    else
        echo -e "${RED}  Entry $entry_num: ${time}ms ❌${NC}"
    fi
done
echo

# Performance summary
metric "Average Recall Latency: ${avg_latency}ms"
if [ $avg_latency -lt 500 ]; then
    success "✅ LATENCY TARGET MET: ${avg_latency}ms < 500ms"
else
    error "❌ LATENCY TARGET MISSED: ${avg_latency}ms ≥ 500ms"
fi
echo

metric "Direct Recall Accuracy: ${recall_accuracy}% (${successful_recalls}/${#RECALL_RESULTS[@]})"
if [ $recall_accuracy -ge 90 ]; then
    success "✅ ACCURACY TARGET MET: ${recall_accuracy}% ≥ 90%"
else
    error "❌ ACCURACY TARGET MISSED: ${recall_accuracy}% < 90%"
fi
echo

metric "Semantic Search Accuracy: ${semantic_accuracy}% (${actual_matches}/${expected_matches})"
if [ $semantic_accuracy -ge 90 ]; then
    success "✅ SEMANTIC ACCURACY TARGET MET: ${semantic_accuracy}% ≥ 90%"
else
    error "❌ SEMANTIC ACCURACY TARGET MISSED: ${semantic_accuracy}% < 90%"
fi

# Step 5: Final Demo Status
echo
echo -e "${BOLD}${BLUE}FINAL DEMO REQUIREMENTS STATUS${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Requirement 1: Working API + demo (3 saved entries, recall verified)
if [ ${#DEMO_ENTRIES[@]} -eq 3 ] && [ $successful_recalls -eq 3 ]; then
    success "✅ REQUIREMENT 1 MET: Working API + 3 saved entries + recall verified"
    info "   • Created: ${#DEMO_ENTRIES[@]}/3 demo entries"
    info "   • Verified: ${successful_recalls}/3 successful recalls"
else
    error "❌ REQUIREMENT 1 FAILED: API/entries/recall issues"
    info "   • Created: ${#DEMO_ENTRIES[@]}/3 demo entries"
    info "   • Verified: ${successful_recalls}/3 successful recalls"
fi

# Requirement 2: <500ms recall latency, ≥90% recall accuracy
latency_met=false
accuracy_met=false

if [ $avg_latency -lt 500 ]; then
    latency_met=true
fi

if [ $recall_accuracy -ge 90 ]; then
    accuracy_met=true
fi

if $latency_met && $accuracy_met; then
    success "✅ REQUIREMENT 2 MET: <500ms latency (${avg_latency}ms) + ≥90% accuracy (${recall_accuracy}%)"
else
    error "❌ REQUIREMENT 2 FAILED: Performance targets not met"
    if ! $latency_met; then
        info "   • Latency: ${avg_latency}ms ≥ 500ms (FAILED)"
    else
        info "   • Latency: ${avg_latency}ms < 500ms (PASSED)"
    fi
    if ! $accuracy_met; then
        info "   • Accuracy: ${recall_accuracy}% < 90% (FAILED)"
    else
        info "   • Accuracy: ${recall_accuracy}% ≥ 90% (PASSED)"
    fi
fi

echo
echo -e "${BOLD}${GREEN}🎯 DEMO SUMMARY${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ${#DEMO_ENTRIES[@]} -eq 3 ] && [ $successful_recalls -eq 3 ] && $latency_met && $accuracy_met; then
    echo -e "${BOLD}${GREEN}🎉 ALL DEMO REQUIREMENTS SATISFIED!${NC}"
    echo -e "${GREEN}✅ Working API with 3 saved entries and verified recall${NC}"
    echo -e "${GREEN}✅ Performance targets met: <500ms latency, ≥90% accuracy${NC}"
    echo
    echo -e "${BOLD}Demo Data Created:${NC}"
    echo -e "${BLUE}• Entry 1: Work preferences (coffee, productivity, morning focus)${NC}"
    echo -e "${BLUE}• Entry 2: Recreation (hiking, outdoors, weekend activities)${NC}"
    echo -e "${BLUE}• Entry 3: Learning (Python programming, hands-on approach)${NC}"
    echo
    echo -e "${BOLD}Performance Achieved:${NC}"
    echo -e "${BLUE}• Average recall latency: ${avg_latency}ms${NC}"
    echo -e "${BLUE}• Direct recall accuracy: ${recall_accuracy}%${NC}"
    echo -e "${BLUE}• Semantic search accuracy: ${semantic_accuracy}%${NC}"
    exit_code=0
else
    echo -e "${BOLD}${YELLOW}⚠️  DEMO REQUIREMENTS PARTIALLY MET${NC}"
    echo -e "${YELLOW}Some targets may need attention for optimal performance.${NC}"
    exit_code=1
fi

echo
echo -e "${PURPLE}Test completed: $(date)${NC}"

# Optional: Clean up demo data
read -p "Clean up demo data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    info "Cleaning up demo entries..."
    for memory_id in "${DEMO_ENTRIES[@]}"; do
        curl -s -X DELETE "$BASE_URL/api/v1/memories/$memory_id" > /dev/null
    done
    success "Demo data cleaned up"
fi

exit $exit_code
