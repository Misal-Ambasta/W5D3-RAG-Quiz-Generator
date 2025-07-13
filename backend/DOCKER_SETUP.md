# Docker Setup for Quiz Generator RAG System

This guide explains how to set up and run the required services (Redis and Weaviate) for the Quiz Generator RAG system using Docker.

## Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- **Git Bash** or **PowerShell** (for Windows users)

## Services Overview

The RAG system requires two main services:

### 1. Redis (Port 6379)
- **Purpose**: Caching service for search results and quiz data
- **Features**: Fast in-memory data store
- **Status**: Required for optimal performance

### 2. Weaviate (Port 8080)
- **Purpose**: Vector database for semantic search
- **Features**: Stores document embeddings and enables vector search
- **Status**: Optional (system works without it but with reduced functionality)

## Quick Start

### Option 1: Automated Setup (Recommended)

**For Windows:**
```bash
# Run the batch file
start_services.bat
```

**For Linux/Mac:**
```bash
# Make script executable
chmod +x start_services.sh

# Run the script
./start_services.sh
```

### Option 2: Manual Setup

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Service Configuration

### Redis Configuration
- **Image**: `redis:latest`
- **Port**: 6379
- **Data Persistence**: Yes (redis_data volume)
- **Container Name**: redis-server

### Weaviate Configuration
- **Image**: `semitechnologies/weaviate:1.25.0`
- **Ports**: 8080 (HTTP), 50051 (gRPC)
- **Data Persistence**: Yes (weaviate_data volume)
- **Container Name**: weaviate-server
- **Authentication**: Anonymous access enabled
- **Vectorizer**: None (using external embeddings)

## Verifying Services

### Check Redis
```bash
# Using Docker
docker exec redis-server redis-cli ping
# Expected output: PONG

# Using curl (if redis-cli not available)
curl -s http://localhost:6379
```

### Check Weaviate
```bash
# Health check
curl http://localhost:8080/v1/.well-known/ready

# Get schema
curl http://localhost:8080/v1/schema

# Check if running
curl http://localhost:8080/v1/.well-known/live
```

## Common Commands

### Starting Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d redis
docker-compose up -d weaviate
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop redis
docker-compose stop weaviate
```

### Monitoring
```bash
# Check status
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f redis
docker-compose logs -f weaviate

# Check resource usage
docker stats
```

### Data Management
```bash
# Remove containers but keep data
docker-compose down

# Remove containers and data (⚠️ Data will be lost!)
docker-compose down -v

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Error: Port 6379 is already in use
# Solution: Stop existing Redis instance or change port

# Check what's using the port
netstat -ano | findstr :6379  # Windows
lsof -i :6379                 # Linux/Mac

# Kill process using port
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

#### 2. Docker Not Running
```bash
# Error: Cannot connect to Docker daemon
# Solution: Start Docker Desktop
```

#### 3. Weaviate Takes Too Long to Start
```bash
# Weaviate can take 30-60 seconds to fully initialize
# Check logs for progress
docker-compose logs -f weaviate
```

#### 4. Permission Issues (Linux/Mac)
```bash
# Make startup script executable
chmod +x start_services.sh

# Fix Docker permissions
sudo usermod -aG docker $USER
# Then log out and back in
```

### Service Health Checks

#### Redis Health Check
```bash
# Method 1: Using Docker exec
docker exec redis-server redis-cli ping

# Method 2: Using Python
python -c "import redis; r=redis.Redis(); print(r.ping())"
```

#### Weaviate Health Check
```bash
# Method 1: Using curl
curl -f http://localhost:8080/v1/.well-known/ready

# Method 2: Using Python
python -c "import requests; print(requests.get('http://localhost:8080/v1/.well-known/ready').status_code)"
```

## Integration with RAG System

### Environment Variables
The RAG system uses these environment variables:

```bash
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Weaviate configuration
WEAVIATE_URL=http://localhost:8080
```

### Application Startup Order
1. **Start Docker services** (Redis + Weaviate)
2. **Wait for services to be ready** (use startup scripts)
3. **Start FastAPI application**

### Graceful Degradation
The RAG system is designed to work even if some services are unavailable:

- **Without Redis**: Caching disabled, slower responses
- **Without Weaviate**: Vector search disabled, falls back to BM25 search
- **With Both**: Full functionality including hybrid search and caching

## Performance Optimization

### Memory Allocation
```yaml
# Add to docker-compose.yml for production
services:
  redis:
    mem_limit: 512m
    
  weaviate:
    mem_limit: 2g
```

### Persistent Storage
Data is automatically persisted using Docker volumes:
- `redis_data`: Redis database files
- `weaviate_data`: Weaviate database and indexes

## Security Considerations

### Development Environment
- Anonymous access enabled for Weaviate
- No authentication for Redis
- Services bound to localhost only

### Production Deployment
For production, consider:
- Enable authentication for both services
- Use environment variables for sensitive configuration
- Implement proper network security
- Regular backups of persistent volumes

## Backup and Recovery

### Backup Data
```bash
# Backup Redis data
docker exec redis-server redis-cli BGSAVE

# Backup Weaviate data
docker exec weaviate-server curl -X POST http://localhost:8080/v1/backups
```

### Restore Data
```bash
# Stop services
docker-compose down

# Restore volumes from backup
docker volume create redis_data
docker volume create weaviate_data

# Start services
docker-compose up -d
```

## Next Steps

1. **Start Services**: Run `start_services.bat` (Windows) or `start_services.sh` (Linux/Mac)
2. **Verify Setup**: Check that both services are running and healthy
3. **Start Application**: Launch your FastAPI application
4. **Test Integration**: Upload a document and try searching

The RAG system will automatically detect and use the available services! 