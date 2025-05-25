# EasyLog Python Server Configuration & Operations Guide

## Server Overview

The EasyLog Python server runs on a Ubuntu-based cloud instance with Docker containerization for all services. The system uses a microservices architecture with multiple interconnected components.

## Architecture Components

### Core Services (Docker Containers)

| Service                | Container Name                     | Port        | Purpose                                     | Status     |
| ---------------------- | ---------------------------------- | ----------- | ------------------------------------------- | ---------- |
| **API Server**         | `easylog-python-server.api`        | 8000        | Main Python FastAPI application with agents | ✅ Running |
| **Nginx Proxy**        | `easylog-python-server.nginx`      | 8001        | Reverse proxy with CORS handling            | ✅ Running |
| **Neo4j Database**     | `easylog-python-server.neo4j`      | 7474, 7687  | Knowledge graph database for Graphiti       | ✅ Running |
| **Weaviate Vector DB** | `easylog-python-server-weaviate-1` | 8080, 50051 | Vector database for document search         | ✅ Running |

### Service Dependencies

```
Flutter App → Nginx (8001) → API Server (8000) → {Neo4j, Weaviate, MySQL}
```

## Deployment Configuration

### Docker Compose Setup

**Location**: `/home/ubuntu/easylog-python-server/docker-compose.yaml`

```yaml
services:
  api:
    build: ./apps/api
    container_name: easylog-python-server.api
    command:
      [
        'uv',
        'run',
        'fastapi',
        'run',
        'src/main.py',
        '--port',
        '8000',
        '--host',
        '0.0.0.0'
      ]
    ports: ['8000:8000']
    environment:
      TZ: Europe/Amsterdam
    env_file: ['.env']
    restart: unless-stopped
    depends_on: [neo4j, weaviate]

  nginx:
    image: nginx:latest
    container_name: easylog-python-server.nginx
    ports: ['8001:80']
    volumes: ['./nginx.conf:/etc/nginx/conf.d/default.conf']
    depends_on: [api]

  neo4j:
    image: neo4j:latest
    container_name: easylog-python-server.neo4j
    ports: ['7474:7474', '7687:7687']
    volumes: ['neo4j:/data']
    environment:
      NEO4J_AUTH: ${NEO4J_USER}/${NEO4J_PASSWORD}
    restart: unless-stopped

  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.30.2
    ports: ['8080:8080', '50051:50051']
    volumes: ['weaviate:/var/lib/weaviate']
    restart: on-failure:0
```

### Environment Configuration

**Location**: `/home/ubuntu/easylog-python-server/.env`

**Key Configuration Variables**:

```bash
# AI/LLM Services
OPENROUTER_API_KEY=sk-or-v1-...     # Primary AI model access
OPENAI_API_KEY=sk-proj-...          # Backup/alternative AI access
ANTHROPIC_API_KEY=sk-ant-api03-...  # Claude model access
MISTRAL_API_KEY=...                 # Mistral model access
GEMINI_API_KEY=...                  # Google Gemini access

# Database Connections
EASYLOG_DB_HOST=10.0.1.210         # MySQL database server
EASYLOG_DB_PORT=3306               # MySQL port
EASYLOG_DB_USER=test_python        # Database user
EASYLOG_DB_NAME=easylog            # Database name
EASYLOG_DB_PASSWORD=...            # Database password

# Knowledge Graph & Vector DB
NEO4J_USER=${NEO4J_USER}           # Neo4j authentication
NEO4J_PASSWORD=${NEO4J_PASSWORD}   # Neo4j authentication

# Application Settings
API_SECRET_KEY=easylog             # Application secret
API_ROOT_PATH=/ai                  # API path prefix
LOG_LEVEL=debug                    # Logging level
TZ=Europe/Amsterdam               # Timezone
```

### Nginx Configuration

**Location**: `/home/ubuntu/easylog-python-server/nginx.conf`

**Key Features**:

- **CORS Handling**: Full CORS support for Flutter app integration
- **Reverse Proxy**: Routes requests to API server
- **SSL Ready**: Configuration prepared for HTTPS
- **Domain**: `staging.easylog.nu`

```nginx
server {
    listen 80;
    server_name localhost staging.easylog.nu;

    location / {
        # CORS preflight handling
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            return 204;
        }

        # Proxy configuration
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers for regular requests
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    }
}
```

## Monitoring & Operations

### Essential Monitoring Commands

#### 1. Container Status Monitoring

```bash
# Check all container status
ssh easylog-python "docker ps"

# Check container health
ssh easylog-python "docker stats --no-stream"

# Check disk usage
ssh easylog-python "df -h"
```

#### 2. Log Monitoring

**Live API Logs** (Most Important):

```bash
# Follow live logs
ssh easylog-python "docker logs easylog-python-server.api -f"

# Recent errors only
ssh easylog-python "docker logs easylog-python-server.api --tail 100 | grep -i error"

# Super Agent activity
ssh easylog-python "docker logs easylog-python-server.api | grep 'super_agent'"

# Agent execution logs
ssh easylog-python "docker logs easylog-python-server.api | grep 'MUMCAgent\|EasyLogAgent\|DebugAgent'"
```

**Other Service Logs**:

```bash
# Nginx proxy logs
ssh easylog-python "docker logs easylog-python-server.nginx --tail 50"

# Neo4j database logs
ssh easylog-python "docker logs easylog-python-server.neo4j --tail 50"

# Weaviate vector database logs
ssh easylog-python "docker logs easylog-python-server-weaviate-1 --tail 50"
```

#### 3. Performance Monitoring

```bash
# Container resource usage
ssh easylog-python "docker stats --no-stream"

# System resources
ssh easylog-python "htop"  # if available
ssh easylog-python "free -h"  # Memory usage
ssh easylog-python "top -bn1 | head -20"  # CPU usage
```

#### 4. Network & Connectivity

```bash
# Check port accessibility
ssh easylog-python "netstat -tlnp | grep -E '8000|8001|7474|7687|8080'"

# Test internal connectivity
ssh easylog-python "curl -s http://localhost:8000/health"
ssh easylog-python "curl -s http://localhost:8001/health"
```

### Service Management

#### Docker Container Management

```bash
# Restart individual services (REQUIRES APPROVAL)
ssh easylog-python "cd easylog-python-server && docker-compose restart api"
ssh easylog-python "cd easylog-python-server && docker-compose restart nginx"
ssh easylog-python "cd easylog-python-server && docker-compose restart neo4j"
ssh easylog-python "cd easylog-python-server && docker-compose restart weaviate"

# Full system restart (REQUIRES APPROVAL)
ssh easylog-python "cd easylog-python-server && docker-compose down && docker-compose up -d"

# View container resource usage
ssh easylog-python "docker stats --no-stream"
```

#### Deployment Updates

```bash
# Check current deployment status
ssh easylog-python "cd easylog-python-server && git status"
ssh easylog-python "cd easylog-python-server && git log --oneline -5"

# Pull latest changes (REQUIRES APPROVAL)
ssh easylog-python "cd easylog-python-server && git pull"

# Rebuild and restart (REQUIRES APPROVAL)
ssh easylog-python "cd easylog-python-server && docker-compose build api && docker-compose up -d"
```

## Troubleshooting Guide

### Common Issues & Solutions

#### 1. API Server Not Responding

```bash
# Check container status
ssh easylog-python "docker ps | grep api"

# Check recent logs for errors
ssh easylog-python "docker logs easylog-python-server.api --tail 50"

# Check if port is accessible
ssh easylog-python "curl -s http://localhost:8000/health || echo 'API not responding'"
```

#### 2. Super Agent Issues

```bash
# Check Super Agent execution
ssh easylog-python "docker logs easylog-python-server.api | grep -i 'super.*agent' | tail -10"

# Check for notification issues
ssh easylog-python "docker logs easylog-python-server.api | grep -i 'notification' | tail -10"

# Check for tool execution errors
ssh easylog-python "docker logs easylog-python-server.api | grep -i 'tool.*error' | tail -10"
```

#### 3. Database Connectivity Issues

```bash
# Check database connection in logs
ssh easylog-python "docker logs easylog-python-server.api | grep -i 'database' | tail -10"

# Check Neo4j status
ssh easylog-python "docker logs easylog-python-server.neo4j --tail 20"

# Check Weaviate status
ssh easylog-python "docker logs easylog-python-server-weaviate-1 --tail 20"
```

#### 4. CORS/Frontend Issues

```bash
# Check nginx logs for CORS issues
ssh easylog-python "docker logs easylog-python-server.nginx --tail 30"

# Test CORS response
ssh easylog-python "curl -H 'Origin: http://localhost:3000' -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: Content-Type' -X OPTIONS http://localhost:8001/"
```

### Error Patterns to Watch For

#### Critical Errors

- `ERROR` in API logs - Application errors
- `FATAL` in any logs - Service failures
- `Connection refused` - Database connectivity issues
- `Out of memory` - Resource exhaustion

#### Warning Patterns

- `WARNING` in logs - Potential issues
- `Timeout` in requests - Performance issues
- `Rate limit` - API quota issues
- `SSL` or `certificate` errors - Security issues

## Performance Optimization

### Resource Monitoring

```bash
# Container resource usage over time
ssh easylog-python "docker stats"

# Disk space monitoring
ssh easylog-python "du -sh /var/lib/docker/volumes/*"

# Log file sizes
ssh easylog-python "docker system df"
```

### Cleanup Operations (REQUIRES APPROVAL)

```bash
# Clean up old logs
ssh easylog-python "docker system prune -f"

# Clean up old images
ssh easylog-python "docker image prune -f"

# Clean up volumes (CAREFUL - may lose data)
ssh easylog-python "docker volume prune -f"
```

## Security Considerations

### Access Control

- **SSH Access**: Only through `ssh easylog-python`
- **Port Security**: Only necessary ports exposed
- **Environment Variables**: Sensitive data in `.env` file
- **Docker Security**: Containers run as non-root where possible

### Monitoring Security

```bash
# Check for failed login attempts
ssh easylog-python "grep 'Failed password' /var/log/auth.log | tail -10"

# Check Docker daemon security
ssh easylog-python "docker info | grep -i security"

# Check open ports
ssh easylog-python "ss -tlnp"
```

## Backup & Recovery

### Important Backup Locations

- **Application Code**: `/home/ubuntu/easylog-python-server/`
- **Environment Config**: `/home/ubuntu/easylog-python-server/.env`
- **Neo4j Data**: Docker volume `neo4j`
- **Weaviate Data**: Docker volume `weaviate`
- **Docker Volumes**: `/var/lib/docker/volumes/`

### Backup Commands (REQUIRES APPROVAL)

```bash
# Backup environment configuration
ssh easylog-python "cd easylog-python-server && cp .env .env.backup_$(date +%Y%m%d%H%M%S)"

# Export Docker volumes
ssh easylog-python "docker run --rm -v easylog-python-server_neo4j:/data -v $(pwd):/backup alpine tar czf /backup/neo4j-backup-$(date +%Y%m%d).tar.gz -C /data ."
```

## Development Workflow

### Code Deployment Process

1. **Local Development**: Make changes locally
2. **Testing**: Test changes thoroughly
3. **Commit**: Commit to git repository
4. **Server Update**: Pull changes on server (REQUIRES APPROVAL)
5. **Rebuild**: Rebuild containers if needed (REQUIRES APPROVAL)
6. **Monitor**: Watch logs for issues

### Safe Deployment Commands

```bash
# Check current server state before changes
ssh easylog-python "cd easylog-python-server && docker ps && git status"

# Pull latest changes (AFTER approval)
ssh easylog-python "cd easylog-python-server && git pull"

# Rebuild API container (AFTER approval)
ssh easylog-python "cd easylog-python-server && docker-compose build api"

# Restart with new code (AFTER approval)
ssh easylog-python "cd easylog-python-server && docker-compose up -d api"

# Monitor deployment
ssh easylog-python "docker logs easylog-python-server.api -f"
```

## Emergency Procedures

### Service Recovery

1. **Identify Issue**: Check logs and container status
2. **Quick Fix**: Restart individual container if possible
3. **Full Recovery**: Restart entire stack if needed
4. **Rollback**: Revert to previous working version if necessary

### Emergency Contacts & Information

- **Server Host**: `easylog-python`
- **Primary Domain**: `staging.easylog.nu`
- **Backup Method**: Git repository + Docker volumes
- **Recovery Time**: Typically 5-10 minutes for restart

### Quick Recovery Commands (USE ONLY IN EMERGENCY)

```bash
# Emergency full restart
ssh easylog-python "cd easylog-python-server && docker-compose restart"

# Emergency service check
ssh easylog-python "cd easylog-python-server && docker-compose ps"

# Emergency log dump
ssh easylog-python "docker logs easylog-python-server.api --tail 100 > /tmp/emergency-logs.txt"
```

## Monitoring Best Practices

### Daily Checks

- Container status: `docker ps`
- Recent errors: `docker logs api --tail 50 | grep ERROR`
- Resource usage: `docker stats --no-stream`
- Super Agent activity: Check for recent executions

### Weekly Checks

- Disk space: `df -h`
- Log rotation: Check log file sizes
- Performance trends: Resource usage over time
- Backup verification: Ensure backups are current

### Monthly Maintenance

- Security updates: Check for system updates
- Docker cleanup: Remove unused images/containers
- Configuration review: Verify environment settings
- Performance optimization: Analyze resource usage patterns

---

**IMPORTANT REMINDER**: Always request approval before executing any commands that modify the server state, restart services, or change configurations. This document provides monitoring and diagnostic commands that are safe to run for system observation.
