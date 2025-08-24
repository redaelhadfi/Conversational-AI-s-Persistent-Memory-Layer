import pytest
import     @pytest.mark.asyncio
    async def test_create_memory(self, test_client: AsyncClient, sample_memory_data):
        """Test creating a memory via API."""
        response = await test_client.post("/api/v1/memories", json=sample_memory_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["content"] == sample_memory_data["content"]
        assert data["context"] == sample_memory_data["context"]
        assert data["tags"] == sample_memory_data["tags"]
        assert data["user_id"] == sample_memory_data["user_id"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asynciofrom httpx import AsyncClient

class TestMemoryAPI:
    """Test memory API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_client: AsyncClient):
        """Test health check endpoint."""
        response = await test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "database" in data
        assert "vector_db" in data
        assert "uptime_seconds" in data
    
    @pytest.mark.asyncio
    async def test_create_memory(self, test_client: AsyncClient, sample_memory_data):
        """Test creating a memory via API."""
        response = await test_client.post("/api/v1/memories", json=sample_memory_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["content"] == sample_memory_data["content"]
        assert data["context"] == sample_memory_data["context"]
        assert data["tags"] == sample_memory_data["tags"]
        assert data["user_id"] == sample_memory_data["user_id"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest_asyncio.async_test
    async def test_get_memory(self, test_client: AsyncClient, sample_memory_data):
        """Test retrieving a memory via API."""
        # Create memory
        create_response = await test_client.post("/api/v1/memories", json=sample_memory_data)
        created_memory = create_response.json()
        memory_id = created_memory["id"]
        
        # Get memory
        response = await test_client.get(f"/api/v1/memories/{memory_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == memory_id
        assert data["content"] == sample_memory_data["content"]
        assert data["access_count"] == 1  # Should increment on access
    
    @pytest_asyncio.async_test
    async def test_get_nonexistent_memory(self, test_client: AsyncClient):
        """Test retrieving a non-existent memory."""
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        response = await test_client.get(f"/api/v1/memories/{fake_uuid}")
        assert response.status_code == 404
    
    @pytest_asyncio.async_test
    async def test_update_memory(self, test_client: AsyncClient, sample_memory_data):
        """Test updating a memory via API."""
        # Create memory
        create_response = await test_client.post("/api/v1/memories", json=sample_memory_data)
        created_memory = create_response.json()
        memory_id = created_memory["id"]
        
        # Update memory
        update_data = {
            "content": "Updated content via API",
            "importance_score": 9
        }
        response = await test_client.put(f"/api/v1/memories/{memory_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == update_data["content"]
        assert data["importance_score"] == update_data["importance_score"]
    
    @pytest_asyncio.async_test
    async def test_delete_memory(self, test_client: AsyncClient, sample_memory_data):
        """Test deleting a memory via API."""
        # Create memory
        create_response = await test_client.post("/api/v1/memories", json=sample_memory_data)
        created_memory = create_response.json()
        memory_id = created_memory["id"]
        
        # Delete memory
        response = await test_client.delete(f"/api/v1/memories/{memory_id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await test_client.get(f"/api/v1/memories/{memory_id}")
        assert get_response.status_code == 404
    
    @pytest_asyncio.async_test
    async def test_search_memories(self, test_client: AsyncClient):
        """Test searching memories via API."""
        # Create test memories
        test_memories = [
            {
                "content": "Meeting about project planning",
                "context": "work",
                "tags": ["meeting", "planning"],
                "importance_score": 8
            },
            {
                "content": "Discussion about vacation plans", 
                "context": "personal",
                "tags": ["vacation", "planning"],
                "importance_score": 5
            }
        ]
        
        for memory_data in test_memories:
            await test_client.post("/api/v1/memories", json=memory_data)
        
        # Search memories
        response = await test_client.get("/api/v1/memories/search?query=meeting&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "memories" in data
        assert "total_count" in data
        assert "search_type" in data
        assert "query_time_ms" in data
        assert len(data["memories"]) >= 1
    
    @pytest_asyncio.async_test
    async def test_get_recent_memories(self, test_client: AsyncClient, sample_memory_data):
        """Test getting recent memories via API."""
        # Create multiple memories
        for i in range(3):
            memory_data = sample_memory_data.copy()
            memory_data["content"] = f"Recent memory {i}"
            await test_client.post("/api/v1/memories", json=memory_data)
        
        # Get recent memories
        response = await test_client.get("/api/v1/memories/recent?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
    
    @pytest_asyncio.async_test
    async def test_get_memory_stats(self, test_client: AsyncClient, sample_memory_data):
        """Test getting memory statistics via API."""
        # Create some test memories
        for i in range(3):
            memory_data = sample_memory_data.copy()
            memory_data["content"] = f"Stats test memory {i}"
            await test_client.post("/api/v1/memories", json=memory_data)
        
        # Get stats
        response = await test_client.get("/api/v1/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_memories" in data
        assert "memories_by_context" in data
        assert "memories_by_day" in data
        assert "avg_access_count" in data
        assert "total_users" in data
        assert data["total_memories"] >= 3
    
    @pytest_asyncio.async_test
    async def test_batch_create_memories(self, test_client: AsyncClient):
        """Test creating multiple memories in batch."""
        batch_data = [
            {
                "content": "Batch memory 1",
                "context": "batch_test",
                "tags": ["batch", "test"],
                "importance_score": 5
            },
            {
                "content": "Batch memory 2",
                "context": "batch_test", 
                "tags": ["batch", "test"],
                "importance_score": 6
            }
        ]
        
        response = await test_client.post("/api/v1/memories/batch", json=batch_data)
        assert response.status_code == 201
        
        data = response.json()
        assert len(data) == 2
        assert all("id" in memory for memory in data)
    
    @pytest_asyncio.async_test
    async def test_invalid_memory_data(self, test_client: AsyncClient):
        """Test creating memory with invalid data."""
        invalid_data = {
            "content": "",  # Empty content should be invalid
            "importance_score": 15  # Out of range (1-10)
        }
        
        response = await test_client.post("/api/v1/memories", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest_asyncio.async_test
    async def test_search_with_filters(self, test_client: AsyncClient):
        """Test searching with various filters."""
        # Create memories with different contexts and users
        test_memories = [
            {
                "content": "Work meeting discussion",
                "context": "work",
                "user_id": "user1",
                "tags": ["meeting"]
            },
            {
                "content": "Personal meeting notes",
                "context": "personal", 
                "user_id": "user2",
                "tags": ["meeting"]
            }
        ]
        
        for memory_data in test_memories:
            await test_client.post("/api/v1/memories", json=memory_data)
        
        # Search with context filter
        response = await test_client.get(
            "/api/v1/memories/search?query=meeting&context=work"
        )
        assert response.status_code == 200
        
        data = response.json()
        work_memories = [m for m in data["memories"] if m["context"] == "work"]
        assert len(work_memories) >= 1
        
        # Search with user filter
        response = await test_client.get(
            "/api/v1/memories/search?query=meeting&user_id=user1"
        )
        assert response.status_code == 200
        
        data = response.json()
        user1_memories = [m for m in data["memories"] if m["user_id"] == "user1"]
        assert len(user1_memories) >= 1
