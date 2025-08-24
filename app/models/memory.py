from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class MemoryBase(BaseModel):
    """Base model for memory."""
    content: str = Field(..., min_length=1, max_length=10000, description="Memory content")
    context: Optional[str] = Field(None, max_length=255, description="Memory context or category")
    tags: Optional[List[str]] = Field(default=[], description="Tags associated with the memory")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
    user_id: Optional[str] = Field(None, max_length=255, description="User or session ID")
    conversation_id: Optional[str] = Field(None, max_length=255, description="Conversation ID")
    importance_score: Optional[int] = Field(default=1, ge=1, le=10, description="Importance score (1-10)")

class MemoryCreate(MemoryBase):
    """Model for creating a memory."""
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()
    
    @validator('tags', pre=True)
    def validate_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v or []

class MemoryUpdate(BaseModel):
    """Model for updating a memory."""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    context: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
    importance_score: Optional[int] = Field(None, ge=1, le=10)

class MemoryResponse(MemoryBase):
    """Model for memory response."""
    id: uuid.UUID = Field(..., description="Memory ID")
    access_count: int = Field(default=0, description="Number of times accessed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")
    vector_id: Optional[str] = Field(None, description="Vector database ID")
    similarity_score: Optional[float] = Field(None, description="Similarity score (for search results)")
    
    class Config:
        from_attributes = True

class MemorySearchRequest(BaseModel):
    """Model for memory search request."""
    query: str = Field(..., min_length=1, description="Search query")
    context: Optional[str] = Field(None, description="Filter by context")
    tags: Optional[List[str]] = Field(default=[], description="Filter by tags")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    conversation_id: Optional[str] = Field(None, description="Filter by conversation ID")
    limit: Optional[int] = Field(default=10, ge=1, le=100, description="Number of results to return")
    min_similarity: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    include_semantic: Optional[bool] = Field(default=True, description="Include semantic search")
    include_keyword: Optional[bool] = Field(default=True, description="Include keyword search")

class MemorySearchResponse(BaseModel):
    """Model for memory search response."""
    memories: List[MemoryResponse] = Field(..., description="List of matching memories")
    total_count: int = Field(..., description="Total number of matches")
    search_type: str = Field(..., description="Type of search performed")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")

class MemoryStats(BaseModel):
    """Model for memory statistics."""
    total_memories: int = Field(..., description="Total number of memories")
    memories_by_context: Dict[str, int] = Field(..., description="Memory count by context")
    memories_by_day: Dict[str, int] = Field(..., description="Memory count by day (last 30 days)")
    top_tags: List[Dict[str, Any]] = Field(..., description="Most used tags")
    avg_access_count: float = Field(..., description="Average access count")
    total_users: int = Field(..., description="Total number of unique users")

class HealthCheck(BaseModel):
    """Model for health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database status")
    vector_db: str = Field(..., description="Vector database status")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")

class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
