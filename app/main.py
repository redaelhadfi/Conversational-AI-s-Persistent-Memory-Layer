from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from .config import settings
from .database.connection import init_db, close_db
from .routers import memories, health
from .services.vector_service import VectorService
from .middleware.rate_limiting import RateLimitMiddleware
from .middleware.logging import LoggingMiddleware

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Conversational AI Memory Service")
    
    # Initialize database
    await init_db()
    
    # Initialize vector service
    vector_service = VectorService()
    await vector_service.initialize()
    app.state.vector_service = vector_service
    
    logger.info("Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down service")
    await close_db()
    if hasattr(app.state, 'vector_service'):
        await app.state.vector_service.close()
    logger.info("Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Conversational AI Memory Service",
    description="Persistent memory layer with structured and semantic search capabilities",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan
)

# Security
security = HTTPBearer()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, calls_per_minute=100)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(health.router)
app.include_router(
    memories.router,
    prefix="/api/v1",
    tags=["memories"]
)

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    if not settings.prometheus_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add request processing metrics."""
    import time
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(process_time)
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=settings.api_workers if not settings.debug else 1
    )
