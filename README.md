# Conversational AI Persistent Memory Layer

A robust persistent memory system for conversational AI that combines structured and semantic search capabilities.

## Features

- 🚀 **Fast API Backend**: Built with FastAPI for high-performance REST APIs
- 🗄️ **Dual Storage**: PostgreSQL for structured data + Qdrant for vector embeddings
- 🔍 **Hybrid Search**: Keyword search + semantic similarity matching
- 🐳 **Dockerized**: Complete containerized deployment
- 🔐 **Secure**: Environment-based configuration with secrets management
- 📊 **Monitoring**: Health checks and logging
- 🧪 **Tested**: Comprehensive test suite

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │     Qdrant      │
│                 │    │                 │    │                 │
│  • REST APIs    │◄──►│  • Metadata     │    │  • Embeddings   │
│  • Auth         │    │  • Structured   │    │  • Semantic     │
│  • Validation   │    │    Search       │    │    Search       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲
         │
    ┌─────────┐
    │ Client  │
    │ Apps    │
    └─────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+ (for local development)

### 1. Clone & Setup

```bash
# Clone the repository
git clone <repository-url>
cd conversational-ai-memory

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
vim .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec api python -m alembic upgrade head

# Create initial collections
docker-compose exec api python scripts/init_collections.py
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Save a memory
curl -X POST "http://localhost:8000/api/v1/memories" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User prefers morning meetings and dislikes long calls",
    "context": "user_preferences",
    "tags": ["meetings", "preferences"]
  }'

# Search memories
curl "http://localhost:8000/api/v1/memories/search?query=meetings&limit=5"
```

## API Endpoints

### Memories Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/memories` | Save a new memory |
| GET | `/api/v1/memories/search` | Search memories (keyword + semantic) |
| GET | `/api/v1/memories/recent` | Get recent memories |
| GET | `/api/v1/memories/{memory_id}` | Get specific memory |
| PUT | `/api/v1/memories/{memory_id}` | Update memory |
| DELETE | `/api/v1/memories/{memory_id}` | Delete memory |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/stats` | Memory statistics |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `QDRANT_HOST` | Qdrant server host | localhost |
| `QDRANT_PORT` | Qdrant server port | 6333 |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | - |
| `API_SECRET_KEY` | Secret key for API authentication | - |
| `LOG_LEVEL` | Logging level | INFO |
| `ENVIRONMENT` | Environment (dev/prod) | dev |

### Database Configuration

The system uses PostgreSQL for structured data and Qdrant for vector storage:

- **PostgreSQL**: Stores memory metadata, timestamps, tags, and relationships
- **Qdrant**: Stores text embeddings for semantic search

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_memory_service.py -v
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Production Deployment

1. **Configure Environment**:
   ```bash
   # Set production values in .env
   ENVIRONMENT=production
   DATABASE_URL=postgresql://user:pass@prod-db:5432/memory_db
   QDRANT_HOST=prod-qdrant
   API_SECRET_KEY=your-super-secure-secret-key
   ```

2. **Deploy with Docker**:
   ```bash
   # Build and deploy
   docker-compose -f docker-compose.prod.yml up -d
   
   # Scale API instances
   docker-compose -f docker-compose.prod.yml up -d --scale api=3
   ```

3. **SSL & Reverse Proxy**:
   Configure nginx or traefik for HTTPS termination.

### Monitoring

- **Health Checks**: Available at `/health`
- **Metrics**: Prometheus metrics at `/metrics`
- **Logs**: Structured JSON logging
- **Database**: Monitor PostgreSQL and Qdrant performance

## Security

### Authentication

The API supports multiple authentication methods:
- API Key authentication (recommended for service-to-service)
- JWT tokens (for user sessions)

### Data Protection

- Environment variables for sensitive data
- Database connection encryption
- API request validation
- Rate limiting

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   ```bash
   # Check if services are running
   docker-compose ps
   
   # Restart services
   docker-compose restart
   ```

2. **Database Migration Errors**:
   ```bash
   # Reset database (dev only!)
   docker-compose down -v
   docker-compose up -d
   ```

3. **Vector Search Not Working**:
   ```bash
   # Check Qdrant status
   curl http://localhost:6333/health
   
   # Recreate collections
   docker-compose exec api python scripts/init_collections.py --force
   ```

### Logs

```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f api

# View last 100 lines
docker-compose logs --tail=100 postgres
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
