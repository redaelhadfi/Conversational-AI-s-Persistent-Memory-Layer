import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.database.connection import get_db, Base
from app.services.vector_service import VectorService
from app.config import settings

# Test database URL
TEST_DATABASE_URL = settings.database_test_url or settings.database_url.replace("memory_db", "memory_test_db")

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped async fixtures."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_vector_service():
    """Create test vector service."""
    vector_service = VectorService()
    vector_service.collection_name = "test_memories"
    await vector_service.initialize()
    yield vector_service
    await vector_service.close()

@pytest.fixture
async def test_client(test_db_session, test_vector_service):
    """Create test HTTP client."""
    
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: test_db_session
    app.state.vector_service = test_vector_service
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing."""
    return {
        "content": "This is a test memory content",
        "context": "test_context",
        "tags": ["test", "memory"],
        "user_id": "test_user",
        "conversation_id": "test_conv",
        "importance_score": 5,
        "metadata": {"test": "data"}
    }
