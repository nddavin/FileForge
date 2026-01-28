# Developer Guide

This guide covers setting up a development environment, contributing to the project, and production deployment.

## Project Structure

```
FileForge/
├── forge_backend/           # Backend FastAPI service
│   ├── __init__.py
│   ├── backend.py           # Application entry point
│   ├── requirements.txt
│   └── Dockerfile
├── forge_frontend/          # Flask frontend service
│   ├── __init__.py
│   ├── frontend.py          # Application entry point
│   ├── templates/           # HTML templates
│   ├── requirements.txt
│   └── Dockerfile
├── file_forge/              # Core file processing service
│   ├── __init__.py
│   ├── api.py               # API endpoints
│   ├── auth.py              # Authentication
│   ├── config.py            # Configuration
│   ├── database.py          # Database models
│   ├── processors.py        # File processors
│   ├── smart_sorter.py      # Sorting logic
│   ├── workflow_engine.py
│   ├── requirements.txt
│   └── Dockerfile
├── multimedia_forge/        # Multimedia processing service
│   ├── __init__.py
│   ├── api.py
│   ├── auth.py
│   ├── config.py
│   ├── processors.py
│   ├── requirements.txt
│   └── Dockerfile
├── docs/                    # Documentation
│   ├── developer-guide.md
│   ├── security-guide.md
│   ├── user-guide.md
│   ├── file-format-support.md
│   └── processing-pipeline.md
├── k8s/                     # Kubernetes manifests
│   ├── deployment.yaml
│   └── ...
├── uploads/                 # Uploaded files (gitignored)
├── .env.example             # Environment template
├── requirements.txt         # Root dependencies
├── docker-compose.yml       # Docker Compose config
└── README.md
```

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- PostgreSQL (optional, SQLite for dev)
- Redis (optional, for caching)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/fileforge.git
   cd fileforge
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r forge_backend/requirements.txt
   pip install -r forge_frontend/requirements.txt
   pip install -r file_forge/requirements.txt
   pip install -r multimedia_forge/requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python -m file_forge.database
   ```

6. **Run development servers**
   ```bash
   # Terminal 1: Backend
   uvicorn file_forge.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Frontend
   python forge_frontend/frontend.py
   ```

### Docker Development

```bash
# Start all services with hot reload
docker-compose up --build

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale file-forge=2
```

## API Development

### Adding New Endpoints

1. Create endpoint in appropriate service:
   ```python
   # file_forge/api.py
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.get("/example")
   async def example_endpoint():
       return {"message": "Hello World"}
   ```

2. Register router in main app:
   ```python
   # file_forge/main.py
   from file_forge.api import router as api_router
   
   app.include_router(api_router, prefix="/api/v1")
   ```

### File Processors

Create new processor in [`file_forge/processors.py`](file_forge/processors.py):

```python
from file_forge.processors import BaseProcessor

class CustomProcessor(BaseProcessor):
    EXTENSIONS = ['.custom']
    
    async def process(self, file_path: str) -> dict:
        # Your processing logic
        return {"result": "processed"}
    
    def extract_metadata(self, file_path: str) -> dict:
        # Extract file metadata
        return {}
```

### Database Models

Add models in [`file_forge/models.py`](file_forge/models.py):

```python
from sqlalchemy import Column, Integer, String, DateTime
from file_forge.database import Base

class CustomModel(Base):
    __tablename__ = "custom_table"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    created_at = Column(DateTime)
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=file_forge --cov-report=html

# Run specific test file
pytest file_forge/tests/test_api.py -v

# Run specific test
pytest file_forge/tests/test_api.py::test_upload -v
```

### Writing Tests

```python
# file_forge/tests/test_example.py
import pytest
from fastapi.testclient import TestClient

def test_example_endpoint():
    from file_forge.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/example")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

## Code Style

### Python (PEP 8)

- Use type hints for all functions
- Docstrings for all public functions
- Max line length: 100 characters

```python
def process_file(file_path: str, options: dict) -> dict:
    """
    Process a file with the given options.
    
    Args:
        file_path: Path to the file
        options: Processing options dictionary
        
    Returns:
        Dictionary containing processing results
    """
    pass
```

### Git Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/new-feature
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "Add new feature"
   ```

3. Push and create PR:
   ```bash
   git push origin feature/new-feature
   ```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

This runs:
- Black (formatting)
- isort (import sorting)
- mypy (type checking)
- flake8 (linting)

## Docker

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker build -t fileforge/forge_backend ./forge_backend

# Build with no cache
docker-compose build --no-cache
```

### Debugging in Docker

```bash
# Run shell in container
docker-compose exec file-forge /bin/bash

# View logs
docker-compose logs -f file-forge

# Check container resources
docker stats
```

---

## 🚀 Operations & Deployment

### Production Build

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Or use production compose file if available
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

See [`.env.example`](.env.example) for required variables.

---

### 🐳 Docker Production Configuration

#### docker-compose.prod.yml (Annotated)

```yaml
version: "3.9"

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - forge_backend
      - forge_frontend
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Backend API Service
  forge_backend:
    build:
      context: ./forge_backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      # Database (use external PostgreSQL in production)
      DATABASE_URL: postgresql://user:password@db:5432/fileforge
      
      # Security keys (use secrets in production)
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      
      # Application settings
      DEBUG: "false"
      HOST: 0.0.0.0
      PORT: 8000
      
      # Storage
      UPLOAD_FOLDER: /app/uploads
      SORTED_FOLDER: /app/sorted
      
      # Redis (external)
      REDIS_URL: redis://redis:6379/0
      
      # CORS
      ALLOWED_ORIGINS: "https://yourdomain.com"
    volumes:
      - uploads_data:/app/uploads
      - sorted_data:/app/sorted
    ports:
      - "8000:8000"
    # Health check configuration
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  # Frontend Service
  forge_frontend:
    build:
      context: ./forge_frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      DEBUG: "false"
      HOST: 0.0.0.0
      PORT: "5000"
      BACKEND_URL: http://forge_backend:8000
      BACKEND_DOWNLOAD_URL: http://forge_backend:8000/download
    ports:
      - "5000:5000"
    depends_on:
      - forge_backend
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:5000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # File Forge Worker
  file-forge:
    build:
      context: ./file_forge
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/fileforge
      REDIS_URL: redis://redis:6379/0
      MAX_WORKERS: 4
    volumes:
      - uploads_data:/app/uploads
      - sorted_data:/app/sorted
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8001/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis (caching and queue)
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # PostgreSQL (production database)
  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: fileforge
      POSTGRES_USER: fileforge
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fileforge -d fileforge"]
      interval: 10s
      timeout: 5s
      retries: 5
    # Performance tuning
    command: |
      postgres
      -c shared_buffers=256MB
      -c max_connections=100
      -c work_mem=16MB
      -c maintenance_work_mem=128MB
      -c effective_cache_size=1GB

volumes:
  uploads_data:
    driver: local
  sorted_data:
    driver: local
  redis_data:
    driver: local
  postgres_data:
    driver: local

networks:
  default:
    driver: bridge
```

---

### 🏥 Health Check Endpoints

#### Backend Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check (liveness) |
| `/ready` | GET | Readiness probe (all dependencies) |
| `/health/detailed` | GET | Detailed status (internal use) |

#### Health Check Response Examples

```json
// GET /health
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}

// GET /ready
{
  "status": "ready",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "storage": "healthy"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}

// GET /health/detailed
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5,
      "connections_active": 10,
      "connections_idle": 20
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 1,
      "memory_used_mb": 50
    },
    "storage": {
      "status": "healthy",
      "disk_free_gb": 100
    }
  },
  "metrics": {
    "requests_total": 10000,
    "errors_total": 5,
    "avg_response_time_ms": 150
  }
}
```

---

### 📈 Scaling Guide

#### Docker Compose Scaling

```bash
# Scale file forge workers
docker-compose up -d --scale file-forge=4

# Scale backend instances
docker-compose up -d --scale forge_backend=3
```

#### Kubernetes Scaling

The project includes Kubernetes manifests in [`k8s/deployment.yaml`](k8s/deployment.yaml) with HPA configurations.

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Manual scaling
kubectl scale deployment fileforge-backend --replicas=5

# View scaling status
kubectl get hpa
```

#### HPA Configuration

```yaml
# Horizontal Pod Autoscaler for Backend
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fileforge-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fileforge-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Scaling Recommendations

| Component | Min Replicas | Max Replicas | Scaling Trigger |
|-----------|-------------|--------------|-----------------|
| Backend API | 2 | 10 | CPU > 70% or RPS > 500 |
| File Forge | 2 | 5 | Queue length > 100 |
| Frontend | 1 | 3 | CPU > 80% |
| Redis | 1 | 1 (cluster) | N/A |
| PostgreSQL | 1 | Read replicas | CPU > 80% |

---

### 🔐 Production Security Variables

#### env.prod.example

```bash
# ===========================================
# PRODUCTION ENVIRONMENT VARIABLES
# ===========================================

# ===========================================
# DATABASE (Use external PostgreSQL)
# ===========================================
DATABASE_URL=postgresql://fileforge:secure_password@db-host:5432/fileforge

# ===========================================
# SECURITY (Generate secure keys!)
# ===========================================
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-256-bit-secret-key-min-32-chars

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-fernet-encryption-key

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your-jwt-secret-key

# Password hashing rounds (12 is recommended)
BCRYPT_ROUNDS=12

# ===========================================
# APPLICATION
# ===========================================
DEBUG=false
HOST=0.0.0.0
PORT=8000

# ===========================================
# FILE STORAGE
# ===========================================
UPLOAD_FOLDER=/app/uploads
SORTED_FOLDER=/app/sorted
MAX_FILE_SIZE=104857600  # 100MB in bytes

# ===========================================
# CORS (Production origins only)
# ===========================================
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# ===========================================
# REDIS (External)
# ===========================================
REDIS_URL=redis://:password@redis-host:6379/0

# ===========================================
# RATE LIMITING
# ===========================================
RATELIMIT_DEFAULT=100 per minute
RATELIMIT_STORAGE_URL=redis://:password@redis-host:6379/1

# ===========================================
# BACKUP CONFIGURATION
# ===========================================
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_MAX_COUNT=100
BACKUP_INTERVAL_HOURS=24

# ===========================================
# MONITORING
# ===========================================
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn

# ===========================================
# EXTERNAL SERVICES (Optional)
# ===========================================
# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-bucket-name

# Email
SMTP_SERVER=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-app-password
```

---

### 🔄 Disaster Recovery

#### Backup Strategy

| Data Type | Backup Frequency | Retention | Storage |
|-----------|-----------------|-----------|---------|
| Database (PostgreSQL) | Daily + WAL | 30 days | S3/GCS |
| Uploaded Files | Daily incremental | 90 days | S3/GCS |
| Configuration | On change | Forever | Git |
| Audit Logs | Real-time | 7+ years | S3 + Glacier |

#### Backup Script

```bash
#!/bin/bash
# backup.sh - Daily backup script

set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups
S3_BUCKET=s3://fileforge-backups

# Database backup
echo "Backing up database..."
pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Uploaded files backup
echo "Backing up uploaded files..."
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz /app/uploads

# Upload to S3
echo "Uploading to S3..."
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz $S3_BUCKET/database/
aws s3 cp $BACKUP_DIR/uploads_backup_$DATE.tar.gz $S3_BUCKET/uploads/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup complete: $DATE"
```

#### Restore Procedure

```bash
#!/bin/bash
# restore.sh - Restore from backup

BACKUP_DATE=$1  # Format: 20240115_120000

# Download from S3
aws s3 cp s3://fileforge-backups/database/db_backup_$BACKUP_DATE.sql.gz /tmp/
aws s3 cp s3://fileforge-backups/uploads/uploads_backup_$BACKUP_DATE.tar.gz /tmp/

# Stop services
docker-compose down

# Restore database
gunzip -k /tmp/db_backup_$BACKUP_DATE.sql.gz
psql $DATABASE_URL < /tmp/db_backup_$BACKUP_DATE.sql

# Restore files
tar -xzf /tmp/uploads_backup_$BACKUP_DATE.tar.gz -C /

# Start services
docker-compose up -d

echo "Restore complete"
```

#### High Availability Setup

```yaml
# docker-compose.ha.yml
services:
  forge_backend:
    deploy:
      mode: replicated
      replicas: 3
    placement:
      constraints:
        - node.role == worker

  # Add load balancer (Traefik/HAProxy)
  traefik:
    image: traefik:v2.9
    command:
      - "--providers.docker"
      - "--entrypoints.web.address=:80"
      - "--providers.docker.swarmmode=true"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Ensure all tests pass
6. Submit pull request

---

## 📚 Additional Documentation

| Document | Description |
|----------|-------------|
| [Security Guide](security-guide.md) | Security features, compliance, RBAC |
| [User Guide](user-guide.md) | End-user documentation |
| [File Format Support](file-format-support.md) | Supported file formats and processing |
| [Processing Pipeline](processing-pipeline.md) | Pipeline architecture and flow |
| [API Documentation](/docs) | OpenAPI documentation (when running) |

---

## 🔗 Enterprise Integrations

FileForge supports seamless integrations with major enterprise systems including CRM, ERP, e-signature, and collaboration platforms.

### Available Integrations

| Integration | Type | Authentication | Description |
|-------------|------|----------------|-------------|
| Salesforce CRM | CRM | OAuth2 | Create leads, contacts, opportunities, upload documents |
| Microsoft Dynamics 365 | CRM | OAuth2 | Manage contacts, accounts, opportunities |
| DocuSign | E-Signature | OAuth2 | Send documents for e-signature, track status |
| Slack | Collaboration | Bearer Token | Send messages, upload files to channels |
| Microsoft Teams | Collaboration | OAuth2 | Send messages, upload files to chats/channels |
| SAP ERP | ERP | Basic Auth | Create materials, purchase orders, documents |
| Oracle ERP Cloud | ERP | OAuth2 | Create suppliers, invoices, upload documents |

### Webhook System

FileForge provides a comprehensive webhook system for real-time event notifications:

```python
from backend.file_processor.services.integrations import (
    WebhookService,
    WebhookPayload,
    WebhookEventType
)

# Create webhook service
webhook_service = WebhookService()

# Subscribe to events
subscription = webhook_service.subscribe(
    name="My Webhook",
    url="https://myapp.com/webhook",
    events=[WebhookEventType.FILE_PROCESSED]
)

# Emit events
payload = WebhookPayload(
    event_type=WebhookEventType.FILE_PROCESSED,
    data={"file_id": "123", "status": "completed"}
)
webhook_service.emit(payload)
```

#### Webhook Events

| Event Type | Description |
|------------|-------------|
| `file.uploaded` | Triggered when a file is uploaded |
| `file.processed` | Triggered when file processing completes |
| `file.deleted` | Triggered when a file is deleted |
| `file.classified` | Triggered when file classification completes |
| `workflow.started` | Triggered when a workflow starts |
| `workflow.completed` | Triggered when a workflow completes |
| `workflow.failed` | Triggered when a workflow fails |
| `integration.connected` | Triggered when an integration connects |
| `integration.error` | Triggered when an integration errors |

### API Endpoints

#### Webhook Management

```bash
# Create webhook
POST /api/v1/integrations/webhooks
{
    "name": "My Webhook",
    "url": "https://example.com/webhook",
    "events": ["file.processed", "workflow.completed"]
}

# List webhooks
GET /api/v1/integrations/webhooks

# Test webhook
POST /api/v1/integrations/webhooks/{id}/test

# Get delivery history
GET /api/v1/integrations/webhooks/{id}/deliveries
```

#### Connect Integrations

```bash
# Connect Salesforce
POST /api/v1/integrations/connect/salesforce
{
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "instance_url": "https://login.salesforce.com"
}

# Connect Slack
POST /api/v1/integrations/connect/slack
{
    "bot_token": "xoxb-your-bot-token"
}

# Connect DocuSign
POST /api/v1/integrations/connect/docusign
{
    "integration_key": "your-integration-key",
    "secret_key": "your-secret-key"
}
```

### Using Connectors Programmatically

```python
from backend.file_processor.services.integrations import (
    SalesforceConnector,
    IntegrationConfig,
    IntegrationType,
    AuthenticationType
)

# Create configuration
config = IntegrationConfig(
    integration_type=IntegrationType.CRM,
    auth_type=AuthenticationType.OAUTH2,
    base_url="https://login.salesforce.com",
    credentials={
        "client_id": "your-client-id",
        "client_secret": "your-client-secret"
    }
)

# Create connector
connector = SalesforceConnector(config)

# Test connection
result = connector.test_connection()
if result.success:
    # Create a lead
    lead_result = connector.create_lead({
        "FirstName": "John",
        "LastName": "Doe",
        "Email": "john@example.com",
        "Company": "Acme Inc"
    })
```

### Adding Custom Integrations

Create a new connector by extending `IntegrationBase`:

```python
from backend.file_processor.services.integrations import (
    IntegrationBase,
    IntegrationConfig,
    IntegrationResult,
    IntegrationType,
    AuthenticationType
)

class CustomConnector(IntegrationBase):
    """Custom integration connector"""
    
    @property
    def integration_name(self) -> str:
        return "Custom Integration"
    
    @property
    def integration_slug(self) -> str:
        return "custom"
    
    def test_connection(self) -> IntegrationResult:
        # Test connection logic
        return IntegrationResult(success=True)
    
    def send(self, endpoint: str, data: dict, method: str = "POST") -> IntegrationResult:
        # Send data to integration
        return IntegrationResult(success=True, data={})
```

### Security Best Practices

1. **Store credentials securely** - Use environment variables or secret management
2. **Validate webhook signatures** - Always verify incoming webhooks
3. **Use HTTPS** - All integrations should use TLS
4. **Implement rate limiting** - Respect API rate limits
5. **Handle errors gracefully** - Implement proper error handling and retries

---
