# Development Guide

This guide provides detailed information for developers working on the Conversational AI Memory Layer.

## Project Structure

```
conversational-ai-memory/
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Configuration settings
│   ├── database/              # Database models and connections
│   │   ├── __init__.py
│   │   ├── connection.py      # Database connection setup
│   │   └── models.py          # SQLAlchemy models
│   ├── models/                # Pydantic models for API
│   │   ├── __init__.py
│   │   └── memory.py          # Memory-related models
│   ├── routers/               # API route handlers
│   │   ├── __init__.py
│   │   ├── health.py          # Health check endpoints
│   │   └── memories.py        # Memory CRUD endpoints
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── memory_service.py  # Memory operations
│   │   └── vector_service.py  # Vector database operations
│   └── middleware/            # Custom middleware
│       ├── __init__.py
│       ├── logging.py         # Request logging
│       └── rate_limit.py      # Rate limiting
├── alembic/                   # Database migrations
│   └── env.py                 # Alembic environment
├── scripts/                   # Utility scripts
│   ├── init_collections.py   # Initialize Qdrant
│   ├── load_sample_data.py   # Load test data
│   └── init-db.sql           # Database initialization
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Test configuration
│   ├── test_api.py           # API endpoint tests
│   └── test_memory_service.py # Service layer tests
├── docker-compose.yml         # Development environment
├── docker-compose.prod.yml    # Production environment
├── Dockerfile                 # Container build instructions
├── requirements.txt           # Python dependencies
├── alembic.ini               # Database migration config
├── pytest.ini               # Test configuration
├── .env.example              # Environment variables template
└── setup.sh                  # Setup script
```

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.9+ (for local development)
- Git

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd conversational-ai-memory
   ./setup.sh
   ```

2. **Configure environment**:
   ```bash
   # Edit .env file with your settings
   vim .env
   
   # Restart services
   docker-compose restart
   ```

### Local Development (without Docker)

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start external services**:
   ```bash
   # PostgreSQL (via Docker)
   docker run -d --name postgres \
     -e POSTGRES_DB=memory_db \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=password \
     -p 5432:5432 postgres:15-alpine
   
   # Qdrant (via Docker)
   docker run -d --name qdrant \
     -p 6333:6333 \
     qdrant/qdrant:v1.7.0
   ```

4. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Start development server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

### Environment Variables

All configuration is handled through environment variables. Copy `.env.example` to `.env` and modify as needed:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `QDRANT_HOST` | Qdrant server host | Yes |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Yes |
| `API_SECRET_KEY` | Secret key for API authentication | Yes |

### Development vs Production

- **Development**: 
  - Debug mode enabled
  - Auto-reload on code changes
  - Detailed error messages
  - API docs available at `/docs`

- **Production**:
  - Debug mode disabled
  - Structured logging
  - Error details hidden
  - Health checks enabled

## Database Management

### Migrations

We use Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Manual Database Operations

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d memory_db

# Backup database
docker-compose exec postgres pg_dump -U postgres memory_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres memory_db < backup.sql
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_memory_service.py -v

# Run tests matching pattern
pytest -k "test_create" -v
```

### Test Structure

- `tests/conftest.py`: Test configuration and fixtures
- `tests/test_api.py`: API endpoint tests
- `tests/test_memory_service.py`: Service layer tests

### Test Database

Tests use a separate test database to avoid interfering with development data. The test database is automatically created and cleaned up.

## API Development

### Adding New Endpoints

1. **Define Pydantic models** in `app/models/`
2. **Add database models** in `app/database/models.py`
3. **Create service methods** in `app/services/`
4. **Add router endpoints** in `app/routers/`
5. **Write tests** in `tests/`

### API Documentation

FastAPI automatically generates OpenAPI documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Vector Database Operations

### Qdrant Management

```bash
# Check Qdrant status
curl http://localhost:6333/health

# List collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/memories

# Search vectors directly
curl -X POST http://localhost:6333/collections/memories/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 10
  }'
```

### Embedding Models

We use OpenAI's text-embedding-3-small model by default. To change:

1. Update `DEFAULT_EMBEDDING_MODEL` in `.env`
2. Update vector dimensions in `vector_service.py`
3. Recreate Qdrant collection

## Monitoring and Debugging

### Logs

```bash
# View all service logs
docker-compose logs

# Follow logs for specific service
docker-compose logs -f api

# View logs with timestamps
docker-compose logs -t api
```

### Health Checks

- **API Health**: GET `/health`
- **Database**: Included in health endpoint
- **Vector DB**: Included in health endpoint

### Metrics (Optional)

If Prometheus is enabled:

- **Metrics endpoint**: `/metrics`
- **Grafana dashboard**: Configure to scrape metrics

## Performance Optimization

### Database

- **Indexes**: Critical indexes are defined in models
- **Connection pooling**: Configured in connection setup
- **Query optimization**: Use `EXPLAIN ANALYZE` for slow queries

### Vector Search

- **Batch operations**: Use batch insert for multiple memories
- **Index optimization**: Qdrant automatically optimizes indexes
- **Similarity thresholds**: Tune for your use case

### API Performance

- **Async operations**: All database operations are async
- **Connection pooling**: Database connections are pooled
- **Rate limiting**: Configurable rate limiting middleware

## Security Considerations

### API Security

- **API Key authentication**: Required for all endpoints
- **CORS**: Configured for allowed origins
- **Rate limiting**: Prevents abuse
- **Input validation**: All inputs validated with Pydantic

### Data Security

- **Environment variables**: Sensitive data in environment
- **Database encryption**: Connection encryption enabled
- **Secrets management**: Use Docker secrets in production

## Deployment

### Development Deployment

```bash
docker-compose up -d
```

### Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale API instances
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

### Environment-Specific Configurations

- **Staging**: Similar to production but with debug logs
- **Production**: Optimized for performance and security

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Check DATABASE_URL format
   - Ensure PostgreSQL is running
   - Verify network connectivity

2. **Vector database issues**:
   - Check Qdrant service status
   - Verify collection exists
   - Check API key if using authentication

3. **Import errors**:
   - Ensure all dependencies installed
   - Check Python path configuration
   - Verify virtual environment activation

### Debug Mode

Enable debug mode in development:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

### Performance Issues

1. **Check database queries**: Enable SQL logging
2. **Monitor memory usage**: Use Docker stats
3. **Profile API endpoints**: Add timing middleware

## Contributing

### Code Style

- **Python**: Follow PEP 8
- **Type hints**: Use type hints for all functions
- **Docstrings**: Document all public functions
- **Comments**: Explain complex logic

### Git Workflow

1. Create feature branch from main
2. Make changes with descriptive commits
3. Add tests for new features
4. Update documentation
5. Submit pull request

### Testing Requirements

- All new features must have tests
- Maintain test coverage above 80%
- Tests must pass in CI/CD pipeline

## Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Qdrant**: https://qdrant.tech/documentation/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Docker**: https://docs.docker.com/

For questions or issues, please create a GitHub issue or contact the development team.
