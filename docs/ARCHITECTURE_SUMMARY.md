# Architecture Summary

This document gives a concise, high-level overview of FileForge's architecture so new contributors can quickly understand core components and responsibilities.

Core components

- API (FastAPI) — `backend/file_processor/main.py`
  - Exposes REST APIs under `/api/v1`
  - Handles authentication, RBAC, and routing to service layers
  - Includes task assignment, storage, and workflow endpoints

- Database (SQLAlchemy + Alembic)
  - Models under `backend/file_processor/models/`
  - Session factory in `backend/file_processor/database.py`
  - Migrations under `backend/migrations/`
  - Task assignment models: TaskWorkflow, TaskAssignment, TeamMember, Skill

- Queue / Workers (Celery)
  - Task queues in `backend/file_processor/queue/`
  - Legacy tasks in `backend/celery_tasks/`
  - Uses Redis as broker and result backend by default
  - Workflow orchestration with chord/group patterns

- File processing services
  - `backend/file_processor/services/` contains extraction, sorting, and integrations
  - Processors are designed to be composable and run in background workers
  - Sermon processor with 5-stage pipeline
  - AI-powered task assignment service
  - Storage sync with Supabase integration
  - Offline backup to Backblaze B2

- Integrations
  - Connectors for Slack, DocuSign, Salesforce, ERP systems live under `services/integrations`

- Frontend (Vite + React)
  - Located in `frontend/` and serves UI at port 3000 in dev

Data flow (brief)

1. User uploads file -> API accepts the file and saves to storage.
2. API creates a task workflow with required task types.
3. Task assignment service uses AI matching to assign tasks to team members.
4. Celery workers execute tasks in parallel (transcription, video processing, etc.).
5. Results are stored in Supabase; notifications sent via integrations.
6. Offline backup to Backblaze B2 for disaster recovery.

Security & compliance

- RBAC implemented via roles and permissions models under `models/rbac.py`.
- JWT-based authentication with token claims embedding roles/permissions.
- Audit logs stored in the DB for sensitive actions.
- RLS policies for storage bucket access control.

Where to read more
- Processing pipeline: `docs/processing-pipeline.md`
- Developer onboarding: `docs/developer-guide.md`
- Task assignment system: `backend/file_processor/services/task_assignment.py`
- RBAC models & API: `backend/file_processor/models/rbac.py` and `backend/file_processor/api/v1/rbac.py`
