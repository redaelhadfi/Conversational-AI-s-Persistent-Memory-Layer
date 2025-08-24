from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
from collections import defaultdict, deque
from typing import Dict, Deque
import structlog

logger = structlog.get_logger()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        client_requests = self.requests[client_ip]
        while client_requests and client_requests[0] < minute_ago:
            client_requests.popleft()
        
        # Check rate limit
        if len(client_requests) >= self.calls_per_minute:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                requests_count=len(client_requests),
                limit=self.calls_per_minute
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute.",
                    "detail": f"Try again in {60 - (current_time - client_requests[0]):.0f} seconds"
                },
                headers={
                    "X-RateLimit-Limit": str(self.calls_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(client_requests[0] + 60))
                }
            )
        
        # Add current request
        client_requests.append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.calls_per_minute - len(client_requests))
        )
        if client_requests:
            response.headers["X-RateLimit-Reset"] = str(int(client_requests[0] + 60))
        
        return response
