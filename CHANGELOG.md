# Changelog

All notable changes to MeterVision are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — Cleanup & hardening review

### Security
- **JWT secret no longer falls back to a public constant.** When `SECRET_KEY`
  is unset, a strong random key is generated per process with a runtime warning,
  instead of signing tokens with `"fallback_insecure_key"`. `SECRET_KEY` (and
  `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`) are now documented in
  `.env.example`.

### Fixed
- **Multi-tenant data leak:** `GET /customers/`, `/buildings/`, and `/places/`
  returned rows from *all* organizations; the matching `POST` routes performed
  no access check. All are now organization-scoped and authorization-checked,
  consistent with projects and meters. *(Behavior change: callers now only see
  their own organizations' data.)*
- **Hardcoded `/home/ogema/MeterReading/uploads`** in the reading-upload path
  broke uploads on any other host. Now uses the configurable `UPLOAD_DIR`.
- **Hardcoded interpreter, `.env.local`, and API paths** in `mqtt_listener.py`
  and `decode_image.py` tied the MQTT pipeline to one machine. The decoder is
  resolved relative to the listener, the interpreter is `sys.executable`, and
  the API base URL is configurable via `METERVISION_API_URL`.
- **Readings were always saved as `Verified` with confidence `1.0`** regardless
  of OCR success. Status now reflects whether a value was actually read, and the
  expected-value match path is distinguished from a low-confidence read.
- `save_upload_file` now creates the destination directory if missing.
- Filename extension parsing is null-safe (no crash on a missing filename).

### Changed
- Migrated startup from the deprecated `@app.on_event("startup")` to a FastAPI
  `lifespan` handler.
- Replaced deprecated Pydantic v1 calls (`from_orm`, `.dict()`) with
  `model_validate` / `model_dump`.
- `GET /api/logs/` uses SQLModel `select(...)` instead of legacy
  `session.query(...)`, newest-first.
- CORS allowed origins are now configurable via `CORS_ALLOW_ORIGINS`.
- Pinned/constrained dependencies in `requirements.txt` for reproducible builds;
  documented the intentional `passlib`/`bcrypt` pin.
- Simplified and de-duplicated the OCR voting logic (removed dead code and an
  unused variable) with no change to the voting outcome.

### Removed
- `app/models_old.py` — orphaned legacy models, never imported, preserved in git
  history.
- `server_start_test.log` — stale committed log containing an old traceback.
- Dead `get_db()` helper and unused `BasicMeterReader`.

### Docs
- New: `docs/KNOWN_ISSUES.md`, `docs/KNOWLEDGE_BASE.md`, `docs/GUIDELINES.md`,
  `docs/APPROACH.md`, and this changelog.
- Corrected OCR model references (Gemma 3 + Qwen, not "Gemini") and clarified
  which parts of the validation pipeline are simulated.
