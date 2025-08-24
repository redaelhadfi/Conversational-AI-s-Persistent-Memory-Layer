#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Script
Tests all functionality of the Conversational AI Memory System
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, List
import sys

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class E2ETestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_data = []
    
    def log(self, message: str, color: str = Colors.BLUE):
        print(f"{color}{message}{Colors.END}")
    
    def success(self, message: str):
        self.log(f"✅ {message}", Colors.GREEN)
        self.passed += 1
    
    def error(self, message: str):
        self.log(f"❌ {message}", Colors.RED)
        self.failed += 1
    
    def info(self, message: str):
        self.log(f"ℹ️  {message}", Colors.YELLOW)
    
    def test_health_check(self) -> bool:
        """Test system health endpoint."""
        self.info("Testing health check endpoint...")
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["status", "database", "vector_db", "uptime_seconds"]
                for field in required_fields:
                    if field not in data:
                        self.error(f"Health check missing field: {field}")
                        return False
                
                # Check status values
                if data["status"] == "healthy" and data["database"] == "healthy" and data["vector_db"] == "healthy":
                    self.success(f"Health check passed - System is healthy")
                    self.info(f"  Uptime: {data['uptime_seconds']:.1f} seconds")
                    return True
                else:
                    self.error(f"Health check failed - Status: {data['status']}, DB: {data['database']}, Vector: {data['vector_db']}")
                    return False
            else:
                self.error(f"Health check failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Health check exception: {e}")
            return False
    
    def test_create_memory(self) -> Dict[str, Any]:
        """Test memory creation."""
        self.info("Testing memory creation...")
        
        test_memory = {
            "content": "End-to-end test: User prefers morning workouts and evening reading sessions.",
            "context": "lifestyle_preferences", 
            "tags": ["exercise", "reading", "routine"],
            "user_id": "e2e_test_user",
            "conversation_id": "e2e_conv_001",
            "importance_score": 7,
            "metadata": {"test_type": "e2e", "timestamp": time.time()}
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/memories",
                json=test_memory,
                headers={"Content-Type": "application/json"},
                timeout=30  # Longer timeout for OpenAI API calls
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Validate response structure
                required_fields = ["id", "content", "created_at", "vector_id"]
                for field in required_fields:
                    if field not in data:
                        self.error(f"Create memory response missing field: {field}")
                        return {}
                
                # Validate content matches
                if data["content"] == test_memory["content"]:
                    self.success(f"Memory created successfully - ID: {data['id']}")
                    self.test_data.append(data)
                    return data
                else:
                    self.error("Created memory content doesn't match input")
                    return {}
            else:
                self.error(f"Memory creation failed with status {response.status_code}: {response.text}")
                return {}
                
        except Exception as e:
            self.error(f"Memory creation exception: {e}")
            return {}
    
    def test_get_memory(self, memory_id: str) -> bool:
        """Test memory retrieval by ID."""
        self.info(f"Testing memory retrieval by ID: {memory_id}")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/memories/{memory_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data["id"] == memory_id:
                    self.success(f"Memory retrieved successfully")
                    self.info(f"  Access count: {data.get('access_count', 0)}")
                    return True
                else:
                    self.error("Retrieved memory ID doesn't match requested ID")
                    return False
            else:
                self.error(f"Memory retrieval failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Memory retrieval exception: {e}")
            return False
    
    def test_recent_memories(self) -> bool:
        """Test recent memories endpoint."""
        self.info("Testing recent memories endpoint...")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/memories/recent?limit=5", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    self.success(f"Recent memories retrieved - Count: {len(data)}")
                    
                    # Validate first memory structure
                    memory = data[0]
                    required_fields = ["id", "content", "created_at"]
                    for field in required_fields:
                        if field not in memory:
                            self.error(f"Recent memory missing field: {field}")
                            return False
                    
                    return True
                else:
                    self.error("Recent memories returned empty or invalid data")
                    return False
            else:
                self.error(f"Recent memories failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Recent memories exception: {e}")
            return False
    
    def test_memory_stats(self) -> bool:
        """Test memory statistics endpoint."""
        self.info("Testing memory statistics endpoint...")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["total_memories", "memories_by_context", "total_users"]
                for field in required_fields:
                    if field not in data:
                        self.error(f"Stats missing field: {field}")
                        return False
                
                self.success(f"Memory statistics retrieved")
                self.info(f"  Total memories: {data['total_memories']}")
                self.info(f"  Total users: {data['total_users']}")
                self.info(f"  Contexts: {list(data['memories_by_context'].keys())}")
                return True
            else:
                self.error(f"Memory stats failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Memory stats exception: {e}")
            return False
    
    def test_search_memories(self) -> bool:
        """Test memory search functionality."""
        self.info("Testing memory search endpoint...")
        
        try:
            # Search for existing content
            search_params = {
                "query": "workout reading routine",
                "limit": 5
            }
            
            response = requests.get(
                f"{BASE_URL}/api/v1/memories/search",
                params=search_params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ["memories", "total_count", "search_type"]
                for field in required_fields:
                    if field not in data:
                        self.error(f"Search response missing field: {field}")
                        return False
                
                self.success(f"Memory search completed")
                self.info(f"  Found {data['total_count']} memories using {data['search_type']}")
                return True
            else:
                self.error(f"Memory search failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Memory search exception: {e}")
            return False
    
    def test_create_multiple_memories(self) -> bool:
        """Test creating multiple memories for comprehensive testing."""
        self.info("Creating multiple test memories...")
        
        test_memories = [
            {
                "content": "User enjoys Italian cuisine, especially pasta carbonara.",
                "context": "food_preferences",
                "tags": ["food", "italian", "pasta"],
                "user_id": "e2e_test_user",
                "conversation_id": "e2e_conv_002"
            },
            {
                "content": "User works as a software engineer at a tech startup in San Francisco.",
                "context": "professional_info",
                "tags": ["career", "technology", "location"],
                "user_id": "e2e_test_user", 
                "conversation_id": "e2e_conv_003"
            },
            {
                "content": "User is planning a vacation to Japan in spring 2025.",
                "context": "travel_plans",
                "tags": ["travel", "japan", "vacation"],
                "user_id": "e2e_test_user",
                "conversation_id": "e2e_conv_004"
            }
        ]
        
        created_count = 0
        for i, memory in enumerate(test_memories):
            try:
                response = requests.post(
                    f"{BASE_URL}/api/v1/memories",
                    json=memory,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 201:
                    created_count += 1
                    data = response.json()
                    self.test_data.append(data)
                else:
                    self.error(f"Failed to create memory {i+1}: {response.status_code}")
                    
            except Exception as e:
                self.error(f"Exception creating memory {i+1}: {e}")
        
        if created_count == len(test_memories):
            self.success(f"Created {created_count} additional test memories")
            return True
        else:
            self.error(f"Only created {created_count} out of {len(test_memories)} memories")
            return False
    
    def test_validation_errors(self) -> bool:
        """Test API validation and error handling."""
        self.info("Testing validation and error handling...")
        
        # Test missing content
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/memories",
                json={"context": "test"},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 422:  # Validation error
                self.success("Validation correctly rejected missing content")
            else:
                self.error(f"Validation should have failed for missing content, got {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Validation test exception: {e}")
            return False
        
        # Test invalid UUID
        try:
            response = requests.get(f"{BASE_URL}/api/v1/memories/invalid-uuid", timeout=10)
            
            if response.status_code == 422:  # Validation error
                self.success("Validation correctly rejected invalid UUID")
                return True
            else:
                self.error(f"Validation should have failed for invalid UUID, got {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"UUID validation test exception: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all end-to-end tests."""
        self.log("🚀 Starting Comprehensive End-to-End Testing", Colors.BOLD)
        self.log(f"Testing against: {BASE_URL}", Colors.BLUE)
        print("="*60)
        
        # Test 1: Health Check
        if not self.test_health_check():
            self.error("Health check failed - stopping tests")
            return self.print_summary()
        
        time.sleep(1)
        
        # Test 2: Create Memory
        memory_data = self.test_create_memory()
        if not memory_data:
            self.error("Memory creation failed - stopping tests")
            return self.print_summary()
        
        time.sleep(1)
        
        # Test 3: Get Memory by ID
        self.test_get_memory(memory_data["id"])
        
        time.sleep(1)
        
        # Test 4: Recent Memories
        self.test_recent_memories()
        
        time.sleep(1)
        
        # Test 5: Memory Stats
        self.test_memory_stats()
        
        time.sleep(1)
        
        # Test 6: Create Multiple Memories
        self.test_create_multiple_memories()
        
        time.sleep(2)
        
        # Test 7: Search Memories
        self.test_search_memories()
        
        time.sleep(1)
        
        # Test 8: Validation and Error Handling
        self.test_validation_errors()
        
        # Final Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print("="*60)
        total_tests = self.passed + self.failed
        
        if self.failed == 0:
            self.log(f"🎉 ALL TESTS PASSED! ({self.passed}/{total_tests})", Colors.GREEN + Colors.BOLD)
            self.log("✅ Conversational AI Memory System is fully functional!", Colors.GREEN)
        else:
            self.log(f"⚠️  TEST RESULTS: {self.passed} passed, {self.failed} failed ({total_tests} total)", Colors.YELLOW + Colors.BOLD)
        
        if self.test_data:
            self.info(f"Created {len(self.test_data)} test memories for validation")
        
        print("="*60)
        return self.failed == 0

if __name__ == "__main__":
    runner = E2ETestRunner()
    success = runner.run_comprehensive_test()
    sys.exit(0 if success else 1)
