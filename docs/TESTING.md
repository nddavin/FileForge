# Testing Guide

This document collects the canonical commands and quick checks to run the test-suite for FileForge's backend and frontend.

Scope
- Backend tests: `backend/tests/`
- Frontend tests: `frontend/src/__tests__/`

Quick commands (macOS / Linux)

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

Install backend dependencies (use `pyproject.toml` or `backend/requirements.txt` depending on your workflow):

```bash
# from project root
pip install -r backend/requirements.txt
# or if you prefer pyproject-based installs
pip install "poetry-core>=1.0" && pip install -e .
```

Run backend unit tests (fast):

```bash
pytest backend/tests/unit -q
```

Run integration tests (may require postgres/redis):

```bash
# using docker-compose to start DBs
docker-compose up -d db redis
# then
pytest backend/tests/integration -q
```

Run full backend test-suite:

```bash
pytest backend/tests/ -q --maxfail=1
```

Coverage report (backend):

```bash
pytest backend/tests/ --cov=backend/file_processor --cov-report=term --cov-report=html
# open htmlcov/index.html
```

Frontend tests (Node.js required):

```bash
cd frontend
npm ci
npm test
```

CI notes
- If CI installs dependencies in a clean environment, make sure `DATABASE_URL` and other required env vars are provided via CI secrets. Use SQLite for fast CI runs where possible.

Troubleshooting
- If tests fail with import errors: ensure virtualenv is activated and `backend/requirements.txt` is installed.
- If DB-related tests fail: start the test DB via `docker-compose up -d db` and ensure migration or initial schema creation is applied.

Need me to run the tests here? I can run a targeted pytest subset once you confirm I may install backend deps into the workspace environment.