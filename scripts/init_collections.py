#!/usr/bin/env python3
"""
Initialize Qdrant collections for the memory service.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.vector_service import VectorService
from app.config import settings
import argparse

async def init_collections(force: bool = False):
    """Initialize Qdrant collections."""
    print("Initializing Qdrant collections...")
    
    vector_service = VectorService()
    
    try:
        await vector_service.initialize()
        print(f"✅ Successfully initialized collection: {settings.collection_name}")
        
        # Get collection info
        info = await vector_service.get_collection_info()
        print(f"Collection info: {info}")
        
    except Exception as e:
        print(f"❌ Failed to initialize collections: {e}")
        sys.exit(1)
    finally:
        await vector_service.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Qdrant collections")
    parser.add_argument("--force", action="store_true", help="Force recreate collections")
    
    args = parser.parse_args()
    
    asyncio.run(init_collections(force=args.force))
