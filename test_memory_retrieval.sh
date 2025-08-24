#!/bin/bash

# Test Memory Retrieval Fix - Focused Test
# Tests the specific fix for the memory retrieval by ID issue

BASE_URL="http://localhost:8000"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}🔍 Testing Memory Retrieval Fix${NC}"
echo "=============================================="

# Get a recent memory ID for testing
echo -e "${YELLOW}Getting recent memory for testing...${NC}"
recent_response=$(curl -s "$BASE_URL/api/v1/memories/recent?limit=1")
memory_id=$(echo "$recent_response" | grep -o '\"id\":\"[^\"]*\"' | cut -d'"' -f4)

if [ -z "$memory_id" ]; then
    echo -e "${RED}❌ No memory found for testing${NC}"
    exit 1
fi

echo -e "${YELLOW}Testing memory retrieval for ID: $memory_id${NC}"

# Test memory retrieval
response=$(curl -s -w "%{http_code}" "$BASE_URL/api/v1/memories/$memory_id")
status_code="${response: -3}"
body="${response%???}"

echo "Response status: $status_code"

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ Memory retrieval SUCCESSFUL${NC}"
    
    # Check if access count was updated
    if echo "$body" | grep -q '\"access_count\":[1-9]'; then
        echo -e "${GREEN}✅ Access count tracking WORKING${NC}"
    else
        echo -e "${YELLOW}⚠️  Access count may not have incremented${NC}"
    fi
    
    # Check if last_accessed was updated
    if echo "$body" | grep -q '\"last_accessed\":\"[^\"]*\"' && ! echo "$body" | grep -q '\"last_accessed\":null'; then
        echo -e "${GREEN}✅ Last accessed timestamp WORKING${NC}"
    else
        echo -e "${YELLOW}⚠️  Last accessed timestamp not set${NC}"
    fi
    
    echo -e "${GREEN}${BOLD}🎉 MEMORY RETRIEVAL FIX CONFIRMED WORKING!${NC}"
    
else
    echo -e "${RED}❌ Memory retrieval FAILED with status $status_code${NC}"
    echo "Response: $body"
    exit 1
fi

echo "=============================================="
echo -e "${BOLD}✅ Memory Retrieval by ID Fix: SUCCESSFUL${NC}"
