# FileForge Backend Documentation

## Overview

FileForge backend is a **FastAPI** application that provides REST APIs for sermon file management, processing, and RBAC. It handles file uploads, media processing, AI analysis, and integrates with external services like Supabase.

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | >=0.115.6 | Web framework |
| SQLAlchemy | >=2.0.36 | ORM |
| Alembic | >=1.14.0 | Database migrations |
| Celery | >=5.4.0 | Background task queue |
| Redis | >=5.2.1 | Message broker & cache |
| Supabase | >=2.27.2 | Auth, database, storage |
| Pydantic | >=2.10.3 | Data validation |
| Python-Jose | >=3.3.0 | JWT handling |
| Uvicorn | >=0.32.0 | ASGI server |

## Project Structure

```
backend/
├── file_processor/              # Main FastAPI application
│   ├── main.py                  # Application entry point
│   ├── database.py              # Database connection & Base
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Common dependencies
│   │   ├── routers.py           # Root router configuration
│   │   └── v1/                  # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── files.py         # File management
│   │       ├── sermons.py       # Sermon processing
│   │       ├── bulk_operations.py
│   │       ├── rbac.py          # Role management
│   │       └── integrations.py  # External integrations
│   ├── core/
│   │   ├── config.py            # Settings
│   │   ├── dependencies.py      # Common dependencies
│   │   ├── security.py          # Password hashing
│   │   └── rbac_security.py     # RBAC implementation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User model
│   │   ├── file.py              # File model
│   │   ├── workflow.py          # Workflow model
│   │   ├── rule.py              # Sorting rules
│   │   └── rbac.py              # Roles & permissions
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py              # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_processor.py    # Generic file processing
│   │   ├── sermon_processor.py  # Sermon-specific processing
│   │   ├── extractor.py         # Metadata extraction
│   │   ├── speaker_identifier.py
│   │   ├── sorter.py            # Smart sorting
│   │   ├── supabase.py          # Supabase integration
│   │   ├── workflow_engine.py   # Workflow orchestration
│   │   └── integrations/        # Third-party integrations
│   │       ├── base.py
│   │       ├── compliance.py
│   │       ├── docusign.py
│   │       ├── dynamics365.py
│   │       ├── erp.py
│   │       ├── ha.py
│   │       ├── monitoring.py
│   │       ├── salesforce.py
│   │       ├── slack.py
│   │       ├── teams.py
│   │       ├── user_experience.py
│   │       └── webhook.py
│   ├── crud/
│   │   ├── __init__.py
│   │   └── user.py              # User CRUD operations
│   ├── security/                # Security utilities
│   ├── utils/                   # Helper functions
│   ├── processors/              # File format processors
│   └── tests/                   # Unit tests
├── celery_tasks/                # Celery background tasks
│   ├── rss_monitor.py
│   └── sermon_workflow.py
├── migrations/                  # Alembic migrations
│   └── *.sql
├── Dockerfile                   # Docker container
├── requirements.txt             # Python dependencies
└── app.db                       # SQLite database (dev)
```

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | OAuth2 password login |
| POST | `/api/v1/auth/register` | User registration |

### Files (`/api/v1/files`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/files/` | List user files |
| POST | `/api/v1/files/upload` | Upload file |
| GET | `/api/v1/files/{id}` | Get file details |
| DELETE | `/api/v1/files/{id}` | Delete file |

### Sermons (`/api/v1/sermons`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sermons/process` | Process sermon (full pipeline) |
| GET | `/api/v1/sermons/{id}/metadata` | Get sermon metadata |
| PATCH | `/api/v1/sermons/{id}/metadata` | Update metadata |
| POST | `/api/v1/sermons/{id}/optimize` | Optimize media file |
| POST | `/api/v1/sermons/{id}/analyze` | Run AI analysis |
| GET | `/api/v1/sermons/{id}/team` | Get assigned team |
| PUT | `/api/v1/sermons/{id}/team` | Update team assignment |
| GET | `/api/v1/sermons/{id}/quality` | Get quality report |
| POST | `/api/v1/sermons/batch/optimize` | Batch optimization |
| GET | `/api/v1/sermons/stats` | Get processing statistics |

### Bulk Operations (`/api/v1/bulk`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/bulk/move` | Move multiple files |
| POST | `/api/v1/bulk/delete` | Delete multiple files |
| POST | `/api/v1/bulk/tag` | Tag multiple files |

### RBAC (`/api/v1/rbac`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/rbac/roles` | List roles |
| POST | `/api/v1/rbac/roles` | Create role |
| GET | `/api/v1/rbac/permissions` | List permissions |

### Integrations (`/api/v1/integrations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/integrations/status` | Check integration health |
| POST | `/api/v1/integrations/sync` | Sync with external service |

## Configuration

### Environment Variables

```bash
# App
APP_NAME=FileForge
VERSION=1.0.0
DEBUG=true

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./app.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/fileforge

# Redis
REDIS_URL=redis://localhost:6379

# File Storage
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# External Services
SENTRY_DSN=
OPENAI_API_KEY=
```

### Settings Class

Settings are managed via [`core/config.py`](backend/file_processor/core/config.py) using Pydantic Settings:

```python
from backend.file_processor.core.config import settings

print(settings.app_name)  # "FileForge"
print(settings.database_url)  # Database connection string
```

## Database Models

### User

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| username | String | Unique username |
| email | String | Unique email |
| hashed_password | String | BCrypt hash |
| roles | String | Comma-separated roles |

### File

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to User |
| filename | String | Original filename |
| file_path | String | Storage path |
| file_type | String | MIME type |
| size | Integer | File size in bytes |
| uploaded_at | DateTime | Upload timestamp |

### Workflow

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Owner |
| name | String | Workflow name |
| description | String | Optional description |
| config | JSON | Workflow configuration |
| status | String | Current status |

### RBAC Models

| Model | Description |
|-------|-------------|
| Role | User roles (admin, manager, user) |
| Permission | Granular permissions (files:upload, files:view) |
| AuditLog | Action logging for compliance |

## RBAC Security

### Permission System

The backend implements JWT-based RBAC with the following permission structure:

**Permission Format:** `resource:action` (e.g., `files:upload`, `users:manage`)

**Common Permissions:**

| Permission | Description |
|------------|-------------|
| `files:upload` | Upload new files |
| `files:view` | View files |
| `files:update` | Modify file metadata |
| `files:delete` | Delete files |
| `files:view_all` | View all users' files |
| `users:view` | View user profiles |
| `users:manage` | Manage users |
| `workflows:create` | Create workflows |
| `workflows:execute` | Execute workflows |

### Role Hierarchy

| Role | Permissions | Description |
|------|-------------|-------------|
| `admin` | All permissions | Full system access |
| `manager` | files:*, users:view, workflows:* | Limited admin access |
| `user` | files:upload, files:view, files:update (own) | Standard user |

### Using RBAC in Routes

```python
from backend.file_processor.core.rbac_security import (
    require_permission,
    require_role,
    get_current_active_user,
)

router = APIRouter()

# Require specific permission
@router.post("/upload")
async def upload_file(
    current_user = Depends(require_permission("files:upload"))
):
    return {"message": "Upload allowed"}

# Require specific role
@router.get("/admin")
async def admin_only(
    current_user = Depends(require_role("admin"))
):
    return {"message": "Admin access"}

# Check ownership
@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    current_user = Depends(get_current_active_user),
    db = Depends(get_db)
):
    # Check if user owns file or has view_all permission
    file = db.query(File).filter(File.id == file_id).first()
    if file.user_id != current_user.id:
        if "files:view_all" not in get_user_permissions(db, current_user):
            raise HTTPException(status_code=403, detail="Access denied")
    return file
```

## Sermon Processing Pipeline

The sermon processor (`services/sermon_processor.py`) implements a 5-stage pipeline:

### Stage 1: Component Detection
- Detects video, audio, transcript, and artwork components
- Identifies file formats and extracts duration

### Stage 2: Location Extraction
- Extracts GPS coordinates from audio/video metadata
- Reverse geocodes to human-readable address

### Stage 3: AI Analysis
- Uses OpenAI to analyze transcripts
- Extracts: series title, sermon title, theme scripture, key themes

### Stage 4: Quality Analysis
- Analyzes video resolution, bitrate, frame rate
- Analyzes audio bitrate, sample rate, channels

### Stage 5: Team Assignment
- Assigns video editor, audio engineer, transcriber
- Queries Supabase for available staff

### Optimization Profiles

| Profile | Description | Use Case |
|---------|-------------|----------|
| `sermon_web` | 720p, 2.5Mbps | Web streaming |
| `sermon_podcast` | Audio only, 96kbps | Podcast distribution |
| `sermon_archive` | High quality, CRF 18 | Archival |

## Services

### FileProcessor
Generic file processing for various formats (PDF, DOCX, images, video).

### SermonProcessor
Sermon-specific pipeline orchestration.

### SupabaseService
Integration with Supabase for auth, database, and storage.

### WorkflowEngine
Executes configurable processing workflows.

### Extractor
Metadata extraction from files (EXIF, ID3, etc.).

## Background Tasks (Celery)

### RSS Monitor
Monitors RSS feeds for new content.

### Sermon Workflow
Runs asynchronous sermon processing tasks.

```bash
# Start Celery worker
celery -A celery_tasks worker --loglevel=info
```

## Development

### Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the API
uvicorn file_processor.main:app --reload --port 8000
```

### Database Migrations

```bash
# Create migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Auto-generate migrations
alembic revision --autogenerate -m "description"
```

### Testing

```bash
pytest tests/ -v
pytest tests/ --cov=file_processor
```

## Docker

```bash
# Build
docker build -t fileforge-backend ./backend

# Run
docker run -p 8000:8000 fileforge-backend
```

## Integration Services

The backend supports integrations with external services:

| Service | Purpose |
|---------|---------|
| **DocuSign** | Document signing |
| **Dynamics 365** | CRM integration |
| **Salesforce** | CRM integration |
| **Slack** | Notifications |
| **Teams** | Collaboration |
| **Webhook** | Custom callbacks |
| **Compliance** | Regulatory compliance |
| **Monitoring** | Sentry/Observability |

## API Documentation

FastAPI automatically generates OpenAPI documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## License

See project root LICENSE file.
