# Approach & Method

The reasoning behind MeterVision's design choices and the method used to
maintain the codebase. This complements `ARCHITECTURE.md` (what the system is)
by explaining *why* and *how we work on it*.

## Product approach

MeterVision delivers "Meter Reading as a Service": camera-equipped devices in
the field photograph utility meters, an AI ensemble reads the value, and the
result flows into a multi-tenant SaaS where organizations manage their own
asset hierarchy. The two hard problems are **reading accuracy** and **tenant
isolation**, and the architecture is organized around solving both.

## Method 1 — Ensemble OCR over single-model trust

No single OCR engine is reliable on real-world meter photos (glare, odd fonts,
rotating dials). Instead of betting on one model, MeterVision runs several and
**votes**:

- Cloud vision models (Gemma 3 27B/12B, Qwen 2.5 VL) provide semantic reading.
- Local engines (EasyOCR, Tesseract) corroborate cheaply and offline.
- An optional **expected value** (captured at install time) acts as ground truth
  for a calibration fast-path.

The voting order encodes a confidence hierarchy: agreement between independent
models is the strongest signal, a cloud model agreeing with a local one is next,
and a lone model is the last resort. The design accepts that any engine can fail
(returning `0.0`) and never lets a failure masquerade as a real "0" reading.

## Method 2 — Defense-in-depth multi-tenancy

Isolation is enforced at multiple layers rather than trusting one:

1. **Schema** — every tenant entity carries an indexed `organization_id`.
2. **Query scoping** — list endpoints filter to the caller's organizations.
3. **Write authorization** — create/delete endpoints assert org membership
   (`_assert_org_access`).
4. **Role bypass is explicit** — Super Admin / Platform Manager bypasses are
   coded as deliberate early returns, not accidental gaps.

The recent cleanup closed three endpoints that violated layer 2/3; the lesson
baked into `GUIDELINES.md` is that **a new endpoint returning cross-tenant rows
is a defect, full stop**.

## Method 3 — Service-first, thin-router structure

HTTP routers translate requests and delegate to static-method service classes
that take a `Session`. This keeps business logic testable without a running
server and lets the same logic be reused by the API, the MQTT decoder, and the
verification scripts.

## Method 4 — Configuration over hardcoding

The codebase previously embedded one developer's absolute paths, interpreter
location, and API host. The method going forward: **every machine-specific value
is an environment variable with a safe default**, documented in `.env.example`.
This is what makes the app portable across dev laptops, CI, and the systemd
deployment.

## Method 5 — Honest documentation

Documentation is maintained as an asset, not marketing. `KNOWN_ISSUES.md`
deliberately records what is *simulated* (the validation pipeline) and what is
*real*, because over-claiming completeness previously hid real bugs. The working
rule: if the code and the docs disagree, that is a bug to be fixed in the same
change — usually by correcting the docs to match reality, then deciding whether
reality should change too.

## How we triage and fix (bug-hunt method)

1. **Read the whole surface first** — models, services, routers, scripts — before
   editing, to map data flow and trust boundaries.
2. **Rank by blast radius** — security (secret handling, authz) and
   data-correctness (tenant leaks, false "verified" data) outrank cosmetics.
3. **Fix in safe order** — config/secret issues, then isolation, then
   correctness, then deprecations and dead code.
4. **Verify behaviorally** — import the app, run a `TestClient` flow that proves
   the fix (e.g. a non-privileged user now gets `403` and sees zero rows), not
   just that it compiles.
5. **Record it** — move the issue to "Resolved" in `KNOWN_ISSUES.md` and note
   any new gotcha in `KNOWLEDGE_BASE.md`.

## Roadmap implied by the method

- Replace the simulated validation/OCR-confidence scaffold with real CV.
- Return a true confidence score from the ensemble and threshold verification on
  it (making the `business/RULES.md` rule real).
- Adopt the org-context middleware uniformly, or retire it.
- Move from auto-create-tables to real migrations for production PostgreSQL.
