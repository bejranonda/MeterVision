# Development Guidelines

Practical rules for working in this repository. Keep changes consistent with
what is already here.

## Environment setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.local      # then fill in keys
python -c "import secrets; print(secrets.token_urlsafe(64))"   # -> SECRET_KEY
uvicorn app.main:app --reload
```

Tesseract must be installed on the host (`apt install tesseract-ocr`).

## Branching & commits

1. Branch off `main` for every change.
2. Write focused commits with imperative subjects
   (`fix(auth): …`, `feat(meters): …`, `docs: …`).
3. Don't commit secrets, `meter_reading.db`, `uploads/`, or logs — they are
   gitignored for a reason.

## Code style

- **Routers stay thin.** Put business logic in `app/services/`; routers handle
  HTTP and call services.
- **Always scope by organization.** Any new list/read endpoint over tenant data
  must filter by the caller's organizations (Super Admin may see all). Use the
  `_user_org_ids` / `_assert_org_access` helpers in `app/main.py` as the
  pattern. A new endpoint that returns rows across all tenants is a bug.
- **Pydantic v2 idioms.** Use `Model.model_validate(...)` and
  `obj.model_dump()` — not the deprecated `from_orm` / `.dict()`.
- **FastAPI lifespan**, not `@app.on_event`. Startup work lives in the
  `lifespan` context manager in `app/main.py`.
- **No hardcoded absolute paths.** Anything machine-specific (paths, URLs,
  hosts, ports) goes through an environment variable with a sensible default.
  See `.env.example`.
- Prefer `session.exec(select(...))` (SQLModel) over the legacy
  `session.query(...)`.

## Security checklist for new endpoints

- [ ] Requires `Depends(get_current_user)` unless intentionally public
      (document public ones in `KNOWN_ISSUES.md`).
- [ ] Verifies org access for tenant-scoped data.
- [ ] Does not echo secrets or full stack traces to the client.
- [ ] Validates/normalizes user-supplied filenames before writing to disk.

## Testing

- `verify_setup.py`, `verify_installation.py`, `verify_ocr.py`, and
  `test_multi_tenant.py` are runnable smoke/integration checks.
- For API behavior, prefer FastAPI's `TestClient`. The OCR engines
  (`easyocr`, `google.generativeai`, `cv2`) are heavy and network-bound; stub
  them in unit tests rather than calling real models.
- Run `python -m py_compile` over changed files as a fast syntax gate.

## Documentation duties

When you change behavior, update the relevant doc in the same PR:
- New/changed gotcha → `docs/KNOWLEDGE_BASE.md`
- New limitation or fixed bug → `docs/KNOWN_ISSUES.md`
- Architecture/flow change → `docs/ARCHITECTURE.md`
- User-facing change → `README.md` and `CHANGELOG.md`

Stale docs are treated as bugs here — the previous state of this repo claimed
"complete data isolation" while leaking three endpoints. Don't let docs drift.
