from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from .connection import Base

class Memory(Base):
    """Memory model for storing conversational AI memories."""
    
    __tablename__ = "memories"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Content
    content = Column(Text, nullable=False, comment="The actual memory content/text")
    context = Column(String(255), nullable=True, comment="Context or category of the memory")
    
    # Metadata
    tags = Column(ARRAY(String), nullable=True, comment="Tags associated with the memory")
    metadata_json = Column(JSON, nullable=True, comment="Additional metadata as JSON")
    
    # Relationships and references
    user_id = Column(String(255), nullable=True, index=True, comment="User or session ID")
    conversation_id = Column(String(255), nullable=True, index=True, comment="Conversation ID")
    
    # Search and retrieval
    importance_score = Column(Integer, default=1, comment="Importance score (1-10)")
    access_count = Column(Integer, default=0, comment="How many times this memory was accessed")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), nullable=True, comment="Last time memory was retrieved")
    
    # Vector database reference
    vector_id = Column(String(255), nullable=True, comment="Reference to vector in Qdrant")
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_memories_created_at', 'created_at'),
        Index('idx_memories_context', 'context'),
        Index('idx_memories_user_id', 'user_id'),
        Index('idx_memories_conversation_id', 'conversation_id'),
        Index('idx_memories_importance', 'importance_score'),
        Index('idx_memories_composite', 'user_id', 'context', 'created_at'),
    )
    
    def to_dict(self):
        """Convert memory to dictionary."""
        return {
            'id': str(self.id),
            'content': self.content,
            'context': self.context,
            'tags': self.tags,
            'metadata': self.metadata_json,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'importance_score': self.importance_score,
            'access_count': self.access_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'vector_id': self.vector_id
        }
    
    def __repr__(self):
        return f"<Memory(id={self.id}, context='{self.context}', created_at={self.created_at})>"
