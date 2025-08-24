import pytest
import pytest_asyncio

from app.services.memory_service import MemoryService
from app.models.memory import MemoryCreate, MemoryUpdate, MemorySearchRequest

@pytest_asyncio.fixture
async def memory_service(test_vector_service):
    """Create memory service instance."""
    return MemoryService(test_vector_service)

class TestMemoryService:
    """Test memory service operations."""
    
    @pytest_asyncio.async_test
    async def test_create_memory(self, test_db_session, memory_service, sample_memory_data):
        """Test creating a memory."""
        memory_create = MemoryCreate(**sample_memory_data)
        memory = await memory_service.create_memory(test_db_session, memory_create)
        
        assert memory.id is not None
        assert memory.content == sample_memory_data["content"]
        assert memory.context == sample_memory_data["context"]
        assert memory.tags == sample_memory_data["tags"]
        assert memory.user_id == sample_memory_data["user_id"]
        assert memory.importance_score == sample_memory_data["importance_score"]
    
    @pytest_asyncio.async_test
    async def test_get_memory(self, test_db_session, memory_service, sample_memory_data):
        """Test retrieving a memory."""
        # Create memory
        memory_create = MemoryCreate(**sample_memory_data)
        created_memory = await memory_service.create_memory(test_db_session, memory_create)
        
        # Retrieve memory
        retrieved_memory = await memory_service.get_memory(test_db_session, created_memory.id)
        
        assert retrieved_memory is not None
        assert retrieved_memory.id == created_memory.id
        assert retrieved_memory.content == sample_memory_data["content"]
        assert retrieved_memory.access_count == 1  # Should increment on access
    
    @pytest_asyncio.async_test
    async def test_update_memory(self, test_db_session, memory_service, sample_memory_data):
        """Test updating a memory."""
        # Create memory
        memory_create = MemoryCreate(**sample_memory_data)
        created_memory = await memory_service.create_memory(test_db_session, memory_create)
        
        # Update memory
        update_data = MemoryUpdate(
            content="Updated content",
            importance_score=8
        )
        updated_memory = await memory_service.update_memory(
            test_db_session, created_memory.id, update_data
        )
        
        assert updated_memory is not None
        assert updated_memory.content == "Updated content"
        assert updated_memory.importance_score == 8
    
    @pytest_asyncio.async_test
    async def test_delete_memory(self, test_db_session, memory_service, sample_memory_data):
        """Test deleting a memory."""
        # Create memory
        memory_create = MemoryCreate(**sample_memory_data)
        created_memory = await memory_service.create_memory(test_db_session, memory_create)
        
        # Delete memory
        success = await memory_service.delete_memory(test_db_session, created_memory.id)
        assert success is True
        
        # Verify deletion
        retrieved_memory = await memory_service.get_memory(
            test_db_session, created_memory.id, update_access=False
        )
        assert retrieved_memory is None
    
    @pytest_asyncio.async_test
    async def test_search_memories(self, test_db_session, memory_service):
        """Test searching memories."""
        # Create test memories
        test_memories = [
            MemoryCreate(
                content="Meeting about project planning",
                context="work",
                tags=["meeting", "planning"],
                importance_score=8
            ),
            MemoryCreate(
                content="Discussion about vacation plans",
                context="personal",
                tags=["vacation", "planning"],
                importance_score=5
            ),
            MemoryCreate(
                content="Project review meeting scheduled",
                context="work",
                tags=["meeting", "review"],
                importance_score=7
            )
        ]
        
        for memory_data in test_memories:
            await memory_service.create_memory(test_db_session, memory_data)
        
        # Search for memories
        search_request = MemorySearchRequest(
            query="meeting",
            limit=10
        )
        
        results, search_type = await memory_service.search_memories(
            test_db_session, search_request
        )
        
        assert len(results) >= 2  # Should find at least 2 memories with "meeting"
        assert all("meeting" in result.content.lower() or 
                  "meeting" in (result.tags or []) for result in results)
    
    @pytest_asyncio.async_test
    async def test_get_recent_memories(self, test_db_session, memory_service, sample_memory_data):
        """Test retrieving recent memories."""
        # Create multiple memories
        for i in range(5):
            memory_data = sample_memory_data.copy()
            memory_data["content"] = f"Test memory {i}"
            memory_create = MemoryCreate(**memory_data)
            await memory_service.create_memory(test_db_session, memory_create)
        
        # Get recent memories
        recent_memories = await memory_service.get_recent_memories(
            test_db_session, limit=3
        )
        
        assert len(recent_memories) == 3
        # Should be ordered by creation time (newest first)
        for i in range(len(recent_memories) - 1):
            assert recent_memories[i].created_at >= recent_memories[i + 1].created_at
    
    @pytest_asyncio.async_test
    async def test_get_memory_stats(self, test_db_session, memory_service, sample_memory_data):
        """Test getting memory statistics."""
        # Create some test memories
        contexts = ["work", "personal", "work", "hobby"]
        for i, context in enumerate(contexts):
            memory_data = sample_memory_data.copy()
            memory_data["content"] = f"Test memory {i}"
            memory_data["context"] = context
            memory_create = MemoryCreate(**memory_data)
            await memory_service.create_memory(test_db_session, memory_create)
        
        # Get stats
        stats = await memory_service.get_memory_stats(test_db_session)
        
        assert stats["total_memories"] == 4
        assert stats["memories_by_context"]["work"] == 2
        assert stats["memories_by_context"]["personal"] == 1
        assert stats["memories_by_context"]["hobby"] == 1
