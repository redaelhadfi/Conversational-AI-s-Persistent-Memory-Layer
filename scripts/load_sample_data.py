#!/usr/bin/env python3
"""
Sample data loader for testing the memory service.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database.connection import AsyncSessionLocal, init_db
from app.services.memory_service import MemoryService
from app.services.vector_service import VectorService
from app.models.memory import MemoryCreate
import random

SAMPLE_MEMORIES = [
    {
        "content": "User prefers morning meetings between 9-11 AM",
        "context": "user_preferences",
        "tags": ["meetings", "schedule", "morning"],
        "user_id": "user123",
        "importance_score": 8
    },
    {
        "content": "Client mentioned they want to focus on data analytics features",
        "context": "project_requirements",
        "tags": ["analytics", "features", "client"],
        "conversation_id": "conv456",
        "importance_score": 9
    },
    {
        "content": "Team decided to use React for the frontend",
        "context": "technical_decisions",
        "tags": ["react", "frontend", "technical"],
        "importance_score": 7
    },
    {
        "content": "Budget constraints mean we need to prioritize core features",
        "context": "project_constraints",
        "tags": ["budget", "priorities", "constraints"],
        "importance_score": 8
    },
    {
        "content": "User had trouble with the login process last week",
        "context": "user_issues",
        "tags": ["login", "issues", "ux"],
        "user_id": "user123",
        "importance_score": 6
    },
    {
        "content": "Meeting scheduled for next Tuesday at 2 PM to review designs",
        "context": "schedule",
        "tags": ["meeting", "design", "review"],
        "importance_score": 5
    },
    {
        "content": "Client expressed interest in mobile app version",
        "context": "business_opportunities",
        "tags": ["mobile", "app", "client"],
        "importance_score": 9
    },
    {
        "content": "Performance issues reported with large dataset queries",
        "context": "technical_issues",
        "tags": ["performance", "database", "queries"],
        "importance_score": 8
    },
    {
        "content": "User prefers dark mode interface",
        "context": "user_preferences",
        "tags": ["ui", "dark_mode", "preferences"],
        "user_id": "user123",
        "importance_score": 4
    },
    {
        "content": "Integration with Slack API is working well",
        "context": "integration_status",
        "tags": ["slack", "api", "integration"],
        "importance_score": 6
    }
]

async def load_sample_data():
    """Load sample data into the memory service."""
    print("Loading sample data...")
    
    # Initialize services
    await init_db()
    vector_service = VectorService()
    await vector_service.initialize()
    memory_service = MemoryService(vector_service)
    
    try:
        async with AsyncSessionLocal() as db:
            created_count = 0
            
            for memory_data in SAMPLE_MEMORIES:
                try:
                    memory_create = MemoryCreate(**memory_data)
                    memory = await memory_service.create_memory(db, memory_create)
                    created_count += 1
                    print(f"✅ Created memory: {memory.id} - {memory.content[:50]}...")
                except Exception as e:
                    print(f"❌ Failed to create memory: {e}")
            
            print(f"\n🎉 Successfully loaded {created_count}/{len(SAMPLE_MEMORIES)} sample memories")
            
    except Exception as e:
        print(f"❌ Failed to load sample data: {e}")
        sys.exit(1)
    finally:
        await vector_service.close()

if __name__ == "__main__":
    asyncio.run(load_sample_data())
