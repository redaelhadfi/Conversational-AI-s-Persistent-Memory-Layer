# API Documentation

The Conversational AI Memory Layer provides a RESTful API for managing persistent memories with both structured and semantic search capabilities.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

All API endpoints require authentication via API key in the header:

```http
Authorization: Bearer your-api-key
```

## Response Format

All responses follow a consistent JSON format:

### Success Response
```json
{
  "data": { ... },
  "status": "success"
}
```

### Error Response
```json
{
  "error": "error_type",
  "message": "Human readable message",
  "detail": "Detailed error information (optional)",
  "timestamp": "2023-08-23T10:30:00Z"
}
```

## Endpoints

### Health Check

#### GET /health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-08-23T10:30:00Z",
  "version": "1.0.0",
  "database": "healthy",
  "vector_db": "healthy",
  "uptime_seconds": 3600.5
}
```

**Status Codes:**
- `200`: Service healthy
- `503`: Service unhealthy

---

### Memory Management

#### POST /api/v1/memories

Create a new memory.

**Request Body:**
```json
{
  "content": "User prefers morning meetings between 9-11 AM",
  "context": "user_preferences",
  "tags": ["meetings", "schedule", "morning"],
  "user_id": "user123",
  "conversation_id": "conv456",
  "importance_score": 8,
  "metadata": {
    "source": "calendar_integration",
    "confidence": 0.95
  }
}
```

**Parameters:**
- `content` (required): The memory content (1-10,000 characters)
- `context` (optional): Category or context (max 255 characters)
- `tags` (optional): Array of tags for categorization
- `user_id` (optional): User or session identifier
- `conversation_id` (optional): Conversation identifier
- `importance_score` (optional): Importance from 1-10 (default: 1)
- `metadata` (optional): Additional metadata as JSON object

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "User prefers morning meetings between 9-11 AM",
  "context": "user_preferences",
  "tags": ["meetings", "schedule", "morning"],
  "user_id": "user123",
  "conversation_id": "conv456",
  "importance_score": 8,
  "access_count": 0,
  "metadata": {
    "source": "calendar_integration",
    "confidence": 0.95
  },
  "created_at": "2023-08-23T10:30:00Z",
  "updated_at": "2023-08-23T10:30:00Z",
  "last_accessed": null,
  "vector_id": "vec_123456"
}
```

**Status Codes:**
- `201`: Memory created successfully
- `400`: Invalid request data
- `422`: Validation error
- `500`: Server error

---

#### GET /api/v1/memories/{memory_id}

Retrieve a specific memory by ID.

**Path Parameters:**
- `memory_id`: UUID of the memory

**Response:**
Same as POST response, but with updated `access_count` and `last_accessed`.

**Status Codes:**
- `200`: Memory found
- `404`: Memory not found
- `400`: Invalid memory ID format

---

#### PUT /api/v1/memories/{memory_id}

Update an existing memory.

**Path Parameters:**
- `memory_id`: UUID of the memory

**Request Body:**
```json
{
  "content": "Updated content",
  "importance_score": 9,
  "tags": ["updated", "important"]
}
```

All fields are optional - only provided fields will be updated.

**Response:**
Updated memory object (same format as POST response).

**Status Codes:**
- `200`: Memory updated successfully
- `404`: Memory not found
- `400`: Invalid request data
- `422`: Validation error

---

#### DELETE /api/v1/memories/{memory_id}

Delete a memory.

**Path Parameters:**
- `memory_id`: UUID of the memory

**Response:**
No content (status code indicates success/failure).

**Status Codes:**
- `204`: Memory deleted successfully
- `404`: Memory not found

---

### Search and Retrieval

#### GET /api/v1/memories/search

Search memories using hybrid approach (keyword + semantic search).

**Query Parameters:**
- `query` (required): Search query string
- `context` (optional): Filter by context
- `user_id` (optional): Filter by user ID
- `conversation_id` (optional): Filter by conversation ID
- `tags` (optional): Filter by tags (can be specified multiple times)
- `limit` (optional): Number of results (1-100, default: 10)
- `min_similarity` (optional): Minimum similarity score (0.0-1.0, default: 0.7)
- `include_semantic` (optional): Include semantic search (default: true)
- `include_keyword` (optional): Include keyword search (default: true)

**Example Request:**
```http
GET /api/v1/memories/search?query=meetings&context=work&user_id=user123&limit=5&min_similarity=0.8
```

**Response:**
```json
{
  "memories": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "content": "User prefers morning meetings between 9-11 AM",
      "context": "user_preferences",
      "tags": ["meetings", "schedule", "morning"],
      "user_id": "user123",
      "similarity_score": 0.95,
      "importance_score": 8,
      "access_count": 5,
      "created_at": "2023-08-23T10:30:00Z",
      "updated_at": "2023-08-23T10:30:00Z",
      "last_accessed": "2023-08-23T15:30:00Z"
    }
  ],
  "total_count": 1,
  "search_type": "hybrid",
  "query_time_ms": 45.2
}
```

**Status Codes:**
- `200`: Search completed successfully
- `400`: Invalid query parameters
- `422`: Validation error

---

#### GET /api/v1/memories/recent

Get recently created memories.

**Query Parameters:**
- `limit` (optional): Number of results (1-100, default: 10)
- `user_id` (optional): Filter by user ID
- `context` (optional): Filter by context

**Response:**
Array of memory objects ordered by creation time (newest first).

**Status Codes:**
- `200`: Memories retrieved successfully
- `400`: Invalid query parameters

---

### Batch Operations

#### POST /api/v1/memories/batch

Create multiple memories in a single request.

**Request Body:**
```json
[
  {
    "content": "First memory content",
    "context": "context1",
    "tags": ["tag1"]
  },
  {
    "content": "Second memory content",
    "context": "context2",
    "tags": ["tag2"]
  }
]
```

**Limitations:**
- Maximum 100 memories per batch
- Individual memory validation applies

**Response:**
Array of created memory objects.

**Status Codes:**
- `201`: Batch created successfully (may include partial failures)
- `400`: Invalid request (e.g., too many memories)
- `422`: Validation error

---

### Statistics

#### GET /api/v1/stats

Get memory statistics and analytics.

**Response:**
```json
{
  "total_memories": 1500,
  "memories_by_context": {
    "user_preferences": 450,
    "work_notes": 320,
    "personal": 180,
    "uncategorized": 550
  },
  "memories_by_day": {
    "2023-08-23": 45,
    "2023-08-22": 38,
    "2023-08-21": 52
  },
  "top_tags": [
    {"tag": "meetings", "count": 234},
    {"tag": "important", "count": 189},
    {"tag": "todo", "count": 145}
  ],
  "avg_access_count": 2.4,
  "total_users": 25
}
```

**Status Codes:**
- `200`: Statistics retrieved successfully
- `500`: Server error

---

## Error Codes

### Common HTTP Status Codes

- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `422`: Validation Error
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error
- `503`: Service Unavailable

### Custom Error Types

- `validation_error`: Request data validation failed
- `not_found`: Requested resource not found
- `rate_limit_exceeded`: Too many requests
- `database_error`: Database operation failed
- `vector_db_error`: Vector database operation failed
- `embedding_error`: Text embedding generation failed

## Rate Limiting

API requests are rate limited to prevent abuse:

- **Default**: 100 requests per minute per IP
- **Headers**: Rate limit info included in response headers
- **Exceeding limit**: Returns 429 status with retry information

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1692795600
```

## Search Behavior

### Semantic Search

Uses OpenAI embeddings to find semantically similar memories:

- **Model**: text-embedding-3-small (1536 dimensions)
- **Similarity**: Cosine similarity
- **Threshold**: Configurable minimum similarity score
- **Performance**: ~50-100ms per query

### Keyword Search

Traditional text-based search:

- **Method**: PostgreSQL LIKE queries
- **Case**: Case-insensitive
- **Wildcards**: Supports partial matches
- **Performance**: ~10-20ms per query

### Hybrid Search

Combines both approaches:

1. Performs semantic search for conceptual matches
2. Performs keyword search for exact matches
3. Merges results, removing duplicates
4. Sorts by relevance (similarity score, importance, recency)

## Pagination

For endpoints returning multiple results:

- **Limit**: Use `limit` parameter (max 100)
- **Offset**: Currently not supported (use filtering instead)
- **Cursor**: Not implemented (future enhancement)

## Data Types and Validation

### Memory Content
- **Type**: String
- **Length**: 1-10,000 characters
- **Required**: Yes
- **Validation**: Non-empty after trimming

### Context
- **Type**: String
- **Length**: 1-255 characters
- **Required**: No
- **Validation**: Alphanumeric, spaces, and common punctuation

### Tags
- **Type**: Array of strings
- **Length**: Each tag 1-50 characters
- **Required**: No
- **Validation**: Alphanumeric and underscores

### Importance Score
- **Type**: Integer
- **Range**: 1-10
- **Default**: 1
- **Validation**: Must be within range

### UUIDs
- **Format**: RFC 4122 compliant
- **Example**: `123e4567-e89b-12d3-a456-426614174000`
- **Validation**: Valid UUID format required

## Performance Considerations

### Query Optimization

- Use specific filters (user_id, context) to reduce search space
- Higher similarity thresholds improve performance
- Limit results appropriately for your use case

### Best Practices

1. **Batch operations**: Use batch endpoints for multiple memories
2. **Appropriate limits**: Don't request more data than needed
3. **Filter usage**: Use context and user filters to narrow searches
4. **Caching**: Implement client-side caching for frequent queries

### Response Times

- **Simple queries**: < 100ms
- **Semantic search**: < 200ms
- **Complex filters**: < 300ms
- **Batch operations**: Scales linearly with batch size

## SDK and Client Libraries

### Python Client Example

```python
import httpx

class MemoryClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    async def create_memory(self, content: str, **kwargs):
        data = {"content": content, **kwargs}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/memories",
                json=data,
                headers=self.headers
            )
            return response.json()
    
    async def search_memories(self, query: str, **params):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/memories/search",
                params={"query": query, **params},
                headers=self.headers
            )
            return response.json()
```

### JavaScript Client Example

```javascript
class MemoryClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async createMemory(content, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/v1/memories`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ content, ...options })
        });
        return response.json();
    }
    
    async searchMemories(query, params = {}) {
        const url = new URL(`${this.baseUrl}/api/v1/memories/search`);
        url.searchParams.set('query', query);
        Object.entries(params).forEach(([key, value]) => {
            url.searchParams.set(key, value);
        });
        
        const response = await fetch(url, {
            headers: this.headers
        });
        return response.json();
    }
}
```

## Webhook Support (Future)

Planned webhook support for real-time notifications:

- Memory created
- Memory updated
- Memory accessed
- Search performed

## Versioning

- **Current version**: v1
- **URL format**: `/api/v1/...`
- **Backward compatibility**: Maintained within major versions
- **Deprecation**: 6-month notice for breaking changes

For questions or support, please refer to the project documentation or create an issue in the repository.
