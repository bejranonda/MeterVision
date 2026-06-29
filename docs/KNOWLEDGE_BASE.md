# MeterVision Knowledge Base

Accumulated, hard-won knowledge about *why* the code is the way it is. Read this
before changing dependencies, auth, or the OCR pipeline — several things here
look wrong until you know the history.

---

## Authentication & secrets

- **`SECRET_KEY` must be set in production.** If it is unset the app generates a
  random key at startup (safe, but tokens reset on every restart and differ
  between worker processes). Generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```
- **`passlib==1.7.4` is pinned with `bcrypt==3.2.2` on purpose.** `passlib`
  1.7.4 reads `bcrypt.__about__.__version__`, which was removed in `bcrypt`
  4.x. Upgrading `bcrypt` alone breaks password hashing with a confusing
  `AttributeError`. Upgrade both together or move to `argon2`/native `bcrypt`.

## File storage

- Uploaded images go to `UPLOAD_DIR` (default `uploads/`, configurable). The
  directory is created at startup and again defensively inside
  `save_upload_file`, so a fresh host won't crash on first upload.
- The MQTT decoder writes to a **tenant-scoped** subfolder:
  `uploads/<device_mac_with_dashes>/<timestamp>_<snapType>.jpeg`.
- Legacy data may contain absolute `/home/ogema/...` image paths. `static/app.js`
  rewrites known legacy prefixes to the API base URL when rendering — keep that
  shim until old rows are migrated.

## OCR ensemble (`app/services/ocr.py`)

- The ensemble is **Gemma 3 27B (Google) + Gemma 3 12B (OpenRouter) + Qwen 2.5
  VL (OpenRouter) + EasyOCR + Tesseract**. (Older docs mention "Gemini 2.0/1.5
  Flash" — that is stale; the code never used Gemini.)
- Every reader returns `0.0` on any failure (missing API key, network error,
  unparseable output). `0.0` therefore means "no reading", not "the meter reads
  zero". The voting logic treats only `> 0` values as votes.
- If `expected_value` is supplied and any engine reproduces it, that value wins
  immediately — this is the calibration fast-path used during installation.
- Voting priority: (1) two AI models agree → (2) Gemma-27B agrees with a local
  engine → (3) local engines agree → (4) strongest available AI model →
  (5) any local engine. This order is intentional; preserve it if refactoring.
- Models are instantiated in `SmartMeterReader.__init__`, and a new
  `SmartMeterReader()` is created per request. `EasyOCRMeterReader.__init__`
  loads a model into memory, so this is **not cheap** — a future optimization is
  to cache a singleton reader.

## Database

- SQLModel auto-creates tables at startup from the model metadata; there are no
  migrations. Schema changes to existing tables require deleting
  `meter_reading.db` (dev) or a real migration tool (prod).
- `echo=True` is set on the engine, so the dev server is very chatty. Set it via
  config before production.
- Every asset carries `organization_id` and an index on it. Org-scoped list
  endpoints filter on this column; Super Admin queries skip the filter.

## MQTT pipeline

- `mqtt_listener.py` subscribes to `v1/devices/me/telemetry` and
  `NE101SensingCam/Snapshot`, then shells out to `decode_image.py` using
  `sys.executable` (the active interpreter) so it works in any virtualenv.
- `decode_image.py` authenticates to the API as the admin user, posts a reading
  via `/meters/{serial}/reading_data`, and **auto-provisions** the meter into
  the "undefined" organization on a 404 before retrying.
- The reading value produced by `decode_image.py` is currently a **mock**
  (`12345.0 + random`). Wiring it to `SmartMeterReader` is a known TODO.

## Conventions

- Services in `app/services/` hold business logic and are static-method classes
  that take a `Session`; routers stay thin.
- Many modules use **function-local imports** (e.g. `from .models import
  UserRoleEnum` inside a route) to dodge circular imports between models. This
  is deliberate; keep it unless you restructure the model package.
