from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings."""
    
    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL connection URL")
    database_test_url: Optional[str] = Field(None, description="Test database URL")
    
    # Vector Database Configuration
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_api_key: Optional[str] = Field(None, description="Qdrant API key")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # API Configuration
    api_secret_key: str = Field(..., description="Secret key for API authentication")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="Number of workers")
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        description="Allowed CORS origins (comma-separated)"
    )
    
    # Rate Limiting
    rate_limit: str = Field(default="100/minute", description="Rate limit")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")
    
    # Application Settings
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=True, description="Debug mode")
    max_memory_length: int = Field(default=10000, description="Max memory content length")
    default_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Default embedding model"
    )
    collection_name: str = Field(default="memories", description="Qdrant collection name")
    
    # Redis Configuration (Optional)
    redis_url: Optional[str] = Field(None, description="Redis URL for caching")
    
    # Monitoring
    prometheus_enabled: bool = Field(default=False, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics port")
    
    # Backup Configuration
    backup_enabled: bool = Field(default=False, description="Enable backups")
    backup_schedule: str = Field(default="0 2 * * *", description="Backup schedule (cron)")
    backup_retention_days: int = Field(default=30, description="Backup retention in days")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if v not in ['development', 'testing', 'production']:
            raise ValueError('Environment must be one of: development, testing, production')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        if v not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError('Invalid log level')
        return v
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

# Create global settings instance
settings = Settings()
