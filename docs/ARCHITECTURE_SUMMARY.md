# Architecture Summary

This document gives a concise, high-level overview of FileForge's architecture so new contributors can quickly understand core components and responsibilities.

Core components

- API (FastAPI) — `backend/file_processor/main.py`
  - Exposes REST APIs under `/api/v1`
  - Handles authentication, RBAC, and routing to service layers

- Database (SQLAlchemy + Alembic)
  - Models under `backend/file_processor/models/`
  - Session factory in `backend/file_processor/database.py`
  - Migrations under `backend/migrations/`

- Queue / Workers (Celery)
  - Celery tasks live in `backend/celery_tasks/`
  - Uses Redis as broker and result backend by default

- File processing services
  - `backend/file_processor/services/` contains extraction, sorting, and integrations
  - Processors are designed to be composable and run in background workers

- Integrations
  - Connectors for Slack, DocuSign, Salesforce, ERP systems live under `services/integrations`

- Frontend (Next.js)
  - Located in `frontend/` and serves UI at port 3000 in dev

Data flow (brief)

1. User uploads file -> API accepts the file and saves to `uploads/`.
2. API enqueues a processing job (Celery) and returns a tracking id.
3. Worker picks up job, extracts metadata, runs sorter & workflow engine.
4. Results are stored and surfaced through API; notifications via integrations when configured.

Security & compliance

- RBAC implemented via roles and permissions models under `models/rbac.py`.
- JWT-based authentication with token claims embedding roles/permissions.
- Audit logs stored in the DB for sensitive actions.

Where to read more
- Processing pipeline: `docs/processing-pipeline.md`
- Developer onboarding: `docs/developer-guide.md`
- RBAC models & API: `backend/file_processor/models/rbac.py` and `backend/file_processor/api/v1/rbac.py`
