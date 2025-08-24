import pytest
from httpx import AsyncClient

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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self, test_client: AsyncClient):
        """Test retrieving a non-existent memory."""
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
        response = await test_client.get(f"/api/v1/memories/{fake_uuid}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
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
    
    @pytest.mark.asyncio
    async def test_search_memories(self, test_client: AsyncClient):
        """Test searching memories via API."""
        # Create test memories
        test_memories = [
            {
                "content": "I love pizza and pasta",
                "context": "food_preferences",
                "tags": ["food", "italian"],
                "user_id": "test_user",
            },
            {
                "content": "I prefer hiking in mountains",
                "context": "activities",
                "tags": ["outdoor", "exercise"],
                "user_id": "test_user",
            }
        ]
        
        # Create memories
        for memory_data in test_memories:
            await test_client.post("/api/v1/memories", json=memory_data)
        
        # Search for food-related content
        response = await test_client.get("/api/v1/memories/search?query=pizza&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "memories" in data
        assert "total_count" in data
        assert "search_type" in data
        assert len(data["memories"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_recent_memories(self, test_client: AsyncClient, sample_memory_data):
        """Test getting recent memories via API."""
        # Create a memory
        await test_client.post("/api/v1/memories", json=sample_memory_data)
        
        # Get recent memories
        response = await test_client.get("/api/v1/memories/recent?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check first memory has required fields
        memory = data[0]
        assert "id" in memory
        assert "content" in memory
        assert "created_at" in memory
    
    @pytest.mark.asyncio
    async def test_get_stats(self, test_client: AsyncClient, sample_memory_data):
        """Test getting memory statistics via API."""
        # Create a memory
        await test_client.post("/api/v1/memories", json=sample_memory_data)
        
        # Get stats
        response = await test_client.get("/api/v1/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_memories" in data
        assert "memories_by_context" in data
        assert "memories_by_day" in data
        assert "avg_access_count" in data
        assert "total_users" in data
        assert data["total_memories"] > 0

class TestMemoryValidation:
    """Test memory validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_create_memory_missing_content(self, test_client: AsyncClient):
        """Test creating memory without content fails."""
        invalid_data = {
            "context": "test",
            "user_id": "test_user"
        }
        response = await test_client.post("/api/v1/memories", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_memory_empty_content(self, test_client: AsyncClient):
        """Test creating memory with empty content fails."""
        invalid_data = {
            "content": "",
            "context": "test",
            "user_id": "test_user"
        }
        response = await test_client.post("/api/v1/memories", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_memory_long_content(self, test_client: AsyncClient):
        """Test creating memory with very long content."""
        long_content = "x" * 15000  # Exceeds max length
        invalid_data = {
            "content": long_content,
            "context": "test",
            "user_id": "test_user"
        }
        response = await test_client.post("/api/v1/memories", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_invalid_uuid_format(self, test_client: AsyncClient):
        """Test getting memory with invalid UUID format."""
        response = await test_client.get("/api/v1/memories/invalid-uuid")
        assert response.status_code == 422  # Validation error
