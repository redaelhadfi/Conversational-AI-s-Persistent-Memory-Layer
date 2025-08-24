#!/bin/bash

# Conversational AI Memory Layer Setup Script
# This script helps set up the development environment

set -e

echo "🚀 Setting up Conversational AI Memory Layer..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your configuration (especially OpenAI API key)"
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-super-secret-key-change-this-in-production/$SECRET_KEY/g" .env
    print_success "Generated random secret key"
else
    print_status ".env file already exists, skipping creation"
fi

# Create secrets directory for production
mkdir -p secrets

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check if services are healthy
print_status "Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL is ready"
else
    print_error "PostgreSQL is not ready"
    docker-compose logs postgres
    exit 1
fi

# Check Qdrant
if curl -f http://localhost:6333/health > /dev/null 2>&1; then
    print_success "Qdrant is ready"
else
    print_error "Qdrant is not ready"
    docker-compose logs qdrant
    exit 1
fi

# Wait a bit more for API to be ready
sleep 5

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "API service is ready"
else
    print_warning "API service might not be ready yet. Checking logs..."
    docker-compose logs api
fi

# Run database migrations
print_status "Running database migrations..."
if docker-compose exec -T api alembic upgrade head > /dev/null 2>&1; then
    print_success "Database migrations completed"
else
    print_warning "Database migrations may have failed. Trying to create tables..."
    docker-compose exec -T api python -c "
import asyncio
from app.database.connection import init_db
asyncio.run(init_db())
"
fi

# Initialize Qdrant collections
print_status "Initializing Qdrant collections..."
if docker-compose exec -T api python scripts/init_collections.py > /dev/null 2>&1; then
    print_success "Qdrant collections initialized"
else
    print_warning "Qdrant collection initialization may have failed"
fi

# Load sample data (optional)
read -p "Do you want to load sample data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Loading sample data..."
    if docker-compose exec -T api python scripts/load_sample_data.py > /dev/null 2>&1; then
        print_success "Sample data loaded"
    else
        print_warning "Sample data loading may have failed"
    fi
fi

echo
print_success "🎉 Setup completed!"
echo
echo "Next steps:"
echo "1. Edit .env file with your OpenAI API key and other configuration"
echo "2. Restart services: docker-compose restart"
echo "3. Test the API: curl http://localhost:8000/health"
echo "4. View API documentation: http://localhost:8000/docs"
echo "5. Check logs: docker-compose logs -f"
echo
echo "Services running:"
echo "  - API: http://localhost:8000"
echo "  - PostgreSQL: localhost:5432"
echo "  - Qdrant: http://localhost:6333"
echo "  - Redis: localhost:6379"
echo
print_status "Happy coding! 🚀"
