from fastapi import APIRouter, Depends
from datetime import datetime
import time
import structlog
from sqlalchemy import text

from ..config import settings
from ..database.connection import get_db
from ..services.vector_service import VectorService
from ..models.memory import HealthCheck

logger = structlog.get_logger()
router = APIRouter()

# Store startup time for uptime calculation
startup_time = time.time()

@router.get("/health", response_model=HealthCheck)
async def health_check(db=Depends(get_db)):
    """Health check endpoint."""
    
    # Check database
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check vector database (get from app state)
    vector_status = "healthy"
    try:
        from ..main import app
        if hasattr(app.state, 'vector_service'):
            vector_healthy = await app.state.vector_service.health_check()
            if not vector_healthy:
                vector_status = "unhealthy"
        else:
            vector_status = "unavailable"
    except Exception as e:
        logger.error(f"Vector database health check failed: {e}")
        vector_status = "unhealthy"
    
    # Determine overall status
    overall_status = "healthy"
    if db_status != "healthy" or vector_status != "healthy":
        overall_status = "unhealthy"
    
    return HealthCheck(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database=db_status,
        vector_db=vector_status,
        uptime_seconds=time.time() - startup_time
    )
