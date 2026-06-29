# Known Issues & Limitations

This document tracks the **honest current state** of MeterVision: what is real,
what is simulated, and what is a known gap. It is intended to prevent the
documentation drift that previously made the codebase look more complete than
it was. Update this file whenever you discover or close an issue.

Legend: 🟥 critical · 🟧 high · 🟨 medium · 🟦 low / by-design

---

## Resolved in the latest cleanup

These were active bugs and have been fixed (see `CHANGELOG.md`):

- 🟥 **JWT secret fell back to a shared constant.** `auth.py` used
  `"fallback_insecure_key"` when `SECRET_KEY` was unset, allowing token forgery.
  Now a strong random key is generated per-process (with a loud warning) and
  `SECRET_KEY` is documented in `.env.example`.
- 🟥 **Hardcoded `/home/ogema/MeterReading/uploads`** in the reading-upload
  path broke every upload on any other host. Now uses the configurable
  `UPLOAD_DIR`.
- 🟥 **Hardcoded interpreter / `.env` / API paths** in `mqtt_listener.py` and
  `decode_image.py` tied the MQTT pipeline to one machine. Now resolved
  relative to the script and via `METERVISION_API_URL`.
- 🟧 **Multi-tenant data leak:** `GET /customers/`, `/buildings/`, `/places/`
  returned every organization's rows, and the matching `POST` routes had no
  access check. Now org-scoped and access-checked, matching projects/meters.
- 🟧 **Readings were always stored as `Verified` / confidence `1.0`,** even when
  the OCR ensemble returned `0.0`. Status now reflects whether a value was read.

---

## Open issues

### 🟧 Validation pipeline is simulated, not real
`app/services/validation_service.py` (FOV, glare, OCR) returns hardcoded
"pass" results and does not analyze the image. `CameraService.capture_test_image`
returns a path to a file that does not exist, so a strict reading of
`validate_fov` (which checks `os.path.exists`) would actually *fail* the
pipeline in a real environment. Treat the installation validation flow as a
**demo scaffold**. Real CV/OCR integration is still TODO.

### 🟧 No real OCR confidence score
`SmartMeterReader.read_meter` returns a single `float`, not a confidence. The
upload route therefore assigns a coarse status (`Verified` if a value was read,
else `Failed`) and a placeholder confidence. The "auto-verify above 95%
confidence" rule described in `business/RULES.md` is **aspirational** — there is
no confidence signal to threshold on yet.

### 🟨 SQLite does not enforce foreign keys by default
A Super Admin (who bypasses org access checks) can create an asset referencing a
non-existent `organization_id`; SQLite will not reject it. Enforce FKs
(`PRAGMA foreign_keys=ON`) or validate the org exists before insert when moving
to production / PostgreSQL.

### 🟨 `POST /api/logs/` is unauthenticated
The log-ingest endpoint accepts anonymous writes (used by `decode_image.py`).
This is convenient for the local MQTT pipeline but means any client on the
network can write log entries. Gate it with an API key or internal-only binding
before exposing the host.

### 🟨 Camera heartbeat endpoint uses JWT, not device auth
`POST /api/installations/cameras/heartbeat` is documented as needing API-key
auth in production but currently relies on JWT/no device identity.

### 🟨 `get_current_user_org_context` middleware is largely unused
`business/RULES.md` and `CLAUDE.md` describe org access being enforced by this
middleware, but the asset routes actually perform inline `RBACService` checks.
The middleware exists in `app/middleware/rbac.py` but is not the live path.
Either adopt it consistently or stop advertising it as the mechanism.

### 🟦 Branding is inconsistent across files
References to "Smartrplace", "Operade", and stray SVG assets remain from earlier
integration work. The canonical product name is **MeterVision**.

### 🟦 Two near-duplicate AI context files
`CLAUDE.md` and `GEMINI.md` are ~95% identical. Keep them in sync or collapse to
one with a symlink/include.

---

## How to use this file
- When you fix something here, move it to the "Resolved" section with a one-line
  note and reference the commit/PR.
- When you find something new, add it with a severity and a concrete file/line
  pointer so the next person can act on it without re-investigating.
