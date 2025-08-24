from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from collections import defaultdict
import time
import asyncio
from typing import Dict

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls: Dict[str, list] = defaultdict(list)
        self.window_size = 60  # 60 seconds
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        
        # Clean old entries
        self.calls[client_ip] = [
            call_time for call_time in self.calls[client_ip]
            if now - call_time < self.window_size
        ]
        
        # Check if rate limit exceeded
        if len(self.calls[client_ip]) >= self.calls_per_minute:
            return True
        
        # Add current call
        self.calls[client_ip].append(now)
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        client_ip = self.get_client_ip(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        if self.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "detail": f"Rate limit: {self.calls_per_minute} requests per minute"
                }
            )
        
        return await call_next(request)
