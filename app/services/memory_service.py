from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import structlog
import uuid

from ..database.models import Memory
from ..models.memory import MemoryCreate, MemoryUpdate, MemorySearchRequest
from .vector_service import VectorService

logger = structlog.get_logger()

class MemoryService:
    """Service for memory CRUD operations and search."""
    
    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
    
    async def create_memory(
        self, 
        db: AsyncSession, 
        memory_data: MemoryCreate
    ) -> Memory:
        """Create a new memory."""
        try:
            # Create database record
            memory = Memory(
                content=memory_data.content,
                context=memory_data.context,
                tags=memory_data.tags,
                metadata_json=memory_data.metadata,
                user_id=memory_data.user_id,
                conversation_id=memory_data.conversation_id,
                importance_score=memory_data.importance_score
            )
            
            db.add(memory)
            await db.flush()  # Get the ID without committing
            
            # Store in vector database
            vector_metadata = {
                "context": memory_data.context,
                "user_id": memory_data.user_id,
                "conversation_id": memory_data.conversation_id,
                "importance_score": memory_data.importance_score,
                "tags": memory_data.tags or []
            }
            
            vector_id = await self.vector_service.store_memory(
                str(memory.id),
                memory_data.content,
                vector_metadata
            )
            
            memory.vector_id = vector_id
            await db.commit()
            await db.refresh(memory)
            
            logger.info(f"Created memory: {memory.id}")
            return memory
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create memory: {e}")
            raise
    
    async def get_memory(
        self, 
        db: AsyncSession, 
        memory_id: uuid.UUID,
        update_access: bool = True
    ) -> Optional[Memory]:
        """Get a memory by ID."""
        try:
            result = await db.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if memory and update_access:
                # Update access tracking
                memory.access_count += 1
                from datetime import datetime, timezone
                memory.last_accessed = datetime.now(timezone.utc)
                
                # Add to session and commit
                db.add(memory)
                await db.commit()
                await db.refresh(memory)
            
            return memory
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to get memory {memory_id}: {e}")
            return None
    
    async def update_memory(
        self, 
        db: AsyncSession, 
        memory_id: uuid.UUID, 
        memory_update: MemoryUpdate
    ) -> Optional[Memory]:
        """Update a memory."""
        try:
            result = await db.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            # Update fields
            update_data = memory_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'metadata':
                    setattr(memory, 'metadata_json', value)
                else:
                    setattr(memory, field, value)
            
            # Update vector database if content changed
            if memory_update.content:
                vector_metadata = {
                    "context": memory.context,
                    "user_id": memory.user_id,
                    "conversation_id": memory.conversation_id,
                    "importance_score": memory.importance_score,
                    "tags": memory.tags or []
                }
                
                await self.vector_service.update_memory(
                    str(memory.id),
                    memory_update.content,
                    vector_metadata
                )
            
            await db.commit()
            await db.refresh(memory)
            
            logger.info(f"Updated memory: {memory.id}")
            return memory
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update memory {memory_id}: {e}")
            raise
    
    async def delete_memory(
        self, 
        db: AsyncSession, 
        memory_id: uuid.UUID
    ) -> bool:
        """Delete a memory."""
        try:
            result = await db.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from vector database
            await self.vector_service.delete_memory(str(memory.id))
            
            # Delete from database
            await db.delete(memory)
            await db.commit()
            
            logger.info(f"Deleted memory: {memory.id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            raise
    
    async def search_memories(
        self,
        db: AsyncSession,
        search_request: MemorySearchRequest
    ) -> Tuple[List[Memory], str]:
        """Search memories using hybrid approach (semantic + keyword)."""
        try:
            memories = []
            search_type = "hybrid"
            
            # Semantic search
            if search_request.include_semantic:
                vector_filters = {}
                if search_request.context:
                    vector_filters["context"] = search_request.context
                if search_request.user_id:
                    vector_filters["user_id"] = search_request.user_id
                if search_request.conversation_id:
                    vector_filters["conversation_id"] = search_request.conversation_id
                
                similar_memories = await self.vector_service.search_similar(
                    search_request.query,
                    limit=search_request.limit,
                    score_threshold=search_request.min_similarity,
                    filters=vector_filters
                )
                
                # Get database records for similar memories
                if similar_memories:
                    memory_ids = [
                        uuid.UUID(mem["memory_id"]) 
                        for mem in similar_memories 
                        if mem.get("memory_id")
                    ]
                    
                    result = await db.execute(
                        select(Memory)
                        .where(Memory.id.in_(memory_ids))
                        .order_by(desc(Memory.importance_score), desc(Memory.created_at))
                    )
                    
                    db_memories = result.scalars().all()
                    
                    # Add similarity scores
                    score_map = {
                        mem["memory_id"]: mem["similarity_score"]
                        for mem in similar_memories
                    }
                    
                    for memory in db_memories:
                        memory.similarity_score = score_map.get(str(memory.id), 0.0)
                    
                    memories.extend(db_memories)
                    search_type = "semantic"
            
            # Keyword search (if no semantic results or semantic disabled)
            if (search_request.include_keyword and 
                (not memories or not search_request.include_semantic)):
                
                query_filters = []
                
                # Text search conditions
                text_conditions = [
                    Memory.content.ilike(f"%{search_request.query}%")
                ]
                
                # Add filters
                if search_request.context:
                    query_filters.append(Memory.context == search_request.context)
                if search_request.user_id:
                    query_filters.append(Memory.user_id == search_request.user_id)
                if search_request.conversation_id:
                    query_filters.append(Memory.conversation_id == search_request.conversation_id)
                if search_request.tags:
                    for tag in search_request.tags:
                        query_filters.append(Memory.tags.contains([tag]))
                
                # Build final query
                final_conditions = text_conditions
                if query_filters:
                    final_conditions.append(and_(*query_filters))
                
                result = await db.execute(
                    select(Memory)
                    .where(or_(*text_conditions) if len(text_conditions) > 1 else text_conditions[0])
                    .where(and_(*query_filters) if query_filters else True)
                    .order_by(desc(Memory.importance_score), desc(Memory.created_at))
                    .limit(search_request.limit)
                )
                
                keyword_memories = result.scalars().all()
                
                # Merge with semantic results (avoid duplicates)
                existing_ids = {memory.id for memory in memories}
                for memory in keyword_memories:
                    if memory.id not in existing_ids:
                        memory.similarity_score = 0.5  # Default for keyword matches
                        memories.append(memory)
                
                if not search_request.include_semantic:
                    search_type = "keyword"
            
            # Sort by similarity score if available, then by importance and date
            memories.sort(
                key=lambda m: (
                    getattr(m, 'similarity_score', 0),
                    m.importance_score,
                    m.created_at
                ),
                reverse=True
            )
            
            # Limit results
            memories = memories[:search_request.limit]
            
            logger.info(f"Search found {len(memories)} memories using {search_type} search")
            return memories, search_type
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise
    
    async def get_recent_memories(
        self,
        db: AsyncSession,
        limit: int = 10,
        user_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[Memory]:
        """Get recent memories."""
        try:
            query_filters = []
            
            if user_id:
                query_filters.append(Memory.user_id == user_id)
            if context:
                query_filters.append(Memory.context == context)
            
            result = await db.execute(
                select(Memory)
                .where(and_(*query_filters) if query_filters else True)
                .order_by(desc(Memory.created_at))
                .limit(limit)
            )
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            raise
    
    async def get_memory_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            # Total count
            total_result = await db.execute(select(func.count(Memory.id)))
            total_memories = total_result.scalar()
            
            # Count by context
            context_result = await db.execute(
                select(Memory.context, func.count(Memory.id))
                .group_by(Memory.context)
            )
            memories_by_context = {
                context or "uncategorized": count 
                for context, count in context_result.fetchall()
            }
            
            # Count by day (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            daily_result = await db.execute(
                select(
                    func.date(Memory.created_at).label('date'),
                    func.count(Memory.id)
                )
                .where(Memory.created_at >= thirty_days_ago)
                .group_by(func.date(Memory.created_at))
                .order_by(func.date(Memory.created_at))
            )
            memories_by_day = {
                str(date): count 
                for date, count in daily_result.fetchall()
            }
            
            # Average access count
            avg_result = await db.execute(select(func.avg(Memory.access_count)))
            avg_access_count = float(avg_result.scalar() or 0)
            
            # Unique users
            users_result = await db.execute(
                select(func.count(func.distinct(Memory.user_id)))
                .where(Memory.user_id.isnot(None))
            )
            total_users = users_result.scalar()
            
            return {
                "total_memories": total_memories,
                "memories_by_context": memories_by_context,
                "memories_by_day": memories_by_day,
                "avg_access_count": avg_access_count,
                "total_users": total_users,
                "top_tags": []  # TODO: Implement tag statistics
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            raise
