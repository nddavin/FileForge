# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- Added `get_db()` helper to `backend/file_processor/database.py` to provide a consistent import for DB sessions.
- Added `API_V1_PREFIX` to settings in `backend/file_processor/core/config.py`.
- Updated OAuth2 token URL in `backend/file_processor/api/deps.py` to use the configured API prefix.
- Added documentation: `docs/TESTING.md`, `docs/ARCHITECTURE_SUMMARY.md`, `docs/BACKEND_README.md`.
