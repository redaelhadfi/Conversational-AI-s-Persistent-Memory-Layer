from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import openai
import numpy as np
from typing import List, Optional, Dict, Any
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

from ..config import settings

logger = structlog.get_logger()

class VectorService:
    """Service for vector database operations using Qdrant."""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.collection_name
        self.embedding_model = settings.default_embedding_model
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize OpenAI client
        openai.api_key = settings.openai_api_key
    
    async def initialize(self):
        """Initialize Qdrant client and create collection."""
        try:
            # Create Qdrant client
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key,
                timeout=30,
                https=False  # Disable HTTPS for local development
            )
            
            # Check if collection exists, create if not
            collections = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.client.get_collections
            )
            
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if not collection_exists:
                await self._create_collection()
            
            logger.info(f"Vector service initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            raise
    
    async def _create_collection(self):
        """Create Qdrant collection."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # text-embedding-3-small dimension
                        distance=Distance.COSINE
                    )
                )
            )
            logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: openai.embeddings.create(
                    input=text,
                    model=self.embedding_model
                )
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def store_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store memory in vector database."""
        try:
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            # Create point
            point = PointStruct(
                id=memory_id,
                vector=embedding,
                payload={
                    "content": content,
                    "memory_id": memory_id,
                    **(metadata or {})
                }
            )
            
            # Store in Qdrant
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            )
            
            logger.info(f"Stored memory in vector DB: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory in vector DB: {e}")
            raise
    
    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar memories."""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Build filter conditions
            query_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Search in Qdrant
            results = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold
                )
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "memory_id": result.payload.get("memory_id"),
                    "content": result.payload.get("content"),
                    "similarity_score": float(result.score),
                    "metadata": {
                        k: v for k, v in result.payload.items() 
                        if k not in ["memory_id", "content"]
                    }
                })
            
            logger.info(f"Found {len(formatted_results)} similar memories for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar memories: {e}")
            raise
    
    async def delete_memory(self, memory_id: str):
        """Delete memory from vector database."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=rest.PointIdsList(points=[memory_id])
                )
            )
            logger.info(f"Deleted memory from vector DB: {memory_id}")
        except Exception as e:
            logger.error(f"Failed to delete memory from vector DB: {e}")
            raise
    
    async def update_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update memory in vector database."""
        try:
            # Delete old version
            await self.delete_memory(memory_id)
            
            # Store updated version
            await self.store_memory(memory_id, content, metadata)
            
        except Exception as e:
            logger.error(f"Failed to update memory in vector DB: {e}")
            raise
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information."""
        try:
            info = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.get_collection(self.collection_name)
            )
            
            return {
                "name": info.config.params.vectors.size,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if vector service is healthy."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.get_collections()
            )
            return True
        except Exception as e:
            logger.error(f"Vector service health check failed: {e}")
            return False
    
    async def close(self):
        """Close the vector service."""
        if self.client:
            try:
                self.client.close()
                logger.info("Vector service closed")
            except Exception as e:
                logger.error(f"Error closing vector service: {e}")
        
        if self.executor:
            self.executor.shutdown(wait=True)
