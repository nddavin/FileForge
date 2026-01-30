# Backend README

Location: `backend/`

Quick start (local):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Run the API
uvicorn file_processor.main:app --reload --port 8000
```

Where things live
- `file_processor/` — FastAPI application code
- `celery_tasks/` — background tasks invoked by workers
- `migrations/` — alembic migrations
- `tests/` — backend unit and integration tests

Important notes
- The app supports SQLite for simple local development; use `DATABASE_URL` to switch to Postgres.
- To run workers use Celery: `celery -A celery_tasks worker --loglevel=info`
