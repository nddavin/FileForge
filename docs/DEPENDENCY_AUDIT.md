# Dependency audit workflow

This repository includes a GitHub Actions workflow at `.github/workflows/dependency-audit.yml`.

What the workflow does

- On pull requests to `master` and weekly via cron it will:
  - run `pip-audit` against `backend/requirements.txt` and upload results
  - run `npm audit` for the `frontend` and upload results
  - run `pytest` against the test suite and upload logs

Run locally

- Python audit:
  python -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip pip-audit
  pip-audit -r backend/requirements.txt

- Frontend audit:
  cd frontend
  npm ci
  npm audit --json

Notes

- The workflow currently uploads raw JSON results as artifacts for manual inspection. You can extend it to fail the job on critical findings if desired.
- I added conservative manifest updates earlier (top-level/ backend / pyproject.toml / frontend/package.json). Run the tests in CI to confirm no runtime breakages.
