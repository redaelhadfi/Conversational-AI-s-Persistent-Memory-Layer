from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import time
import structlog

from ..database.connection import get_db
from ..services.memory_service import MemoryService
from ..services.vector_service import VectorService
from ..models.memory import (
    MemoryCreate, MemoryUpdate, MemoryResponse, 
    MemorySearchRequest, MemorySearchResponse, MemoryStats
)

logger = structlog.get_logger()
router = APIRouter()

def get_memory_service() -> MemoryService:
    """Get memory service instance."""
    from ..main import app
    vector_service = app.state.vector_service
    return MemoryService(vector_service)

@router.post("/memories", response_model=MemoryResponse, status_code=201)
async def create_memory(
    memory: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Create a new memory."""
    try:
        created_memory = await memory_service.create_memory(db, memory)
        return MemoryResponse(**created_memory.to_dict())
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to create memory")

@router.get("/memories/search", response_model=MemorySearchResponse)
async def search_memories(
    query: str = Query(..., description="Search query"),
    context: Optional[str] = Query(None, description="Filter by context"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    include_semantic: bool = Query(True, description="Include semantic search"),
    include_keyword: bool = Query(True, description="Include keyword search"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Search memories using hybrid approach."""
    start_time = time.time()
    
    search_request = MemorySearchRequest(
        query=query,
        context=context,
        user_id=user_id,
        conversation_id=conversation_id,
        limit=limit,
        min_similarity=min_similarity,
        include_semantic=include_semantic,
        include_keyword=include_keyword,
        tags=tags or []
    )
    
    memories, search_type = await memory_service.search_memories(db, search_request)
    
    query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return MemorySearchResponse(
        memories=[MemoryResponse(**memory.to_dict()) for memory in memories],
        total_count=len(memories),
        search_type=search_type,
        query_time_ms=query_time
    )

@router.get("/memories/recent", response_model=List[MemoryResponse])
async def get_recent_memories(
    limit: int = Query(10, ge=1, le=100, description="Number of recent memories"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    context: Optional[str] = Query(None, description="Filter by context"),
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get recent memories."""
    memories = await memory_service.get_recent_memories(
        db, limit=limit, user_id=user_id, context=context
    )
    
    return [MemoryResponse(**memory.to_dict()) for memory in memories]

@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: uuid.UUID = Path(..., description="Memory ID"),
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get a memory by ID."""
    memory = await memory_service.get_memory(db, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return MemoryResponse(**memory.to_dict())

@router.put("/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: uuid.UUID = Path(..., description="Memory ID"),
    memory_update: MemoryUpdate = ...,
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Update a memory."""
    memory = await memory_service.update_memory(db, memory_id, memory_update)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return MemoryResponse(**memory.to_dict())

@router.delete("/memories/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: uuid.UUID = Path(..., description="Memory ID"),
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Delete a memory."""
    success = await memory_service.delete_memory(db, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")

@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Get memory statistics."""
    stats = await memory_service.get_memory_stats(db)
    return MemoryStats(**stats)

# Batch operations
@router.post("/memories/batch", response_model=List[MemoryResponse], status_code=201)
async def create_memories_batch(
    memories: List[MemoryCreate],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Create multiple memories in batch."""
    if len(memories) > 100:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 100")
    
    created_memories = []
    for memory_data in memories:
        try:
            memory = await memory_service.create_memory(db, memory_data)
            created_memories.append(memory)
        except Exception as e:
            logger.error(f"Failed to create memory in batch: {e}")
            # Continue with other memories
            continue
    
    return [MemoryResponse(**memory.to_dict()) for memory in created_memories]
