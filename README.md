# MeterVision

**Read utility meters from photos.** MeterVision turns camera snapshots of
electricity, gas, water, and heat meters into structured readings, then stores
them in a multi-tenant FastAPI backend with per-organization access control.

It is built for "meter reading as a service": a service provider runs one
instance, and each customer organization manages its own sites, meters, and
staff without seeing anyone else's data.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

## Why it exists

A single OCR engine is not reliable on real meter photos. Dials rotate, digits
sit behind scratched plastic, and glare wipes out whole readings. MeterVision
runs several readers on each image and takes a vote, so one model's bad guess
does not become the recorded value. When a reading is captured during install,
the known starting value is fed back in as a hint to improve accuracy.

## What it does

- **OCR ensemble** — combines Gemma 3 (27B and 12B), Qwen 2.5 VL, EasyOCR, and
  Tesseract, then picks the reading they most agree on.
- **Multi-tenant data model** — a six-level hierarchy (Organization → Project →
  Customer → Building → Place → Meter) with every record scoped to one
  organization.
- **Role-based access control** — five roles spanning platform-wide and
  per-organization permissions.
- **Camera install workflow** — a mobile-first installer flow that walks a
  technician through connection, framing, glare, and a first test reading
  before the camera goes live.
- **MQTT ingestion** — a listener that decodes snapshots published by IoT
  cameras and posts the readings back to the API.

## How it works

```
Camera ──MQTT──> Listener ──> Decoder ──> API ──> OCR ensemble ──> Reading
                                           │
                                  Multi-tenant database
```

1. A camera publishes a base64 snapshot over MQTT.
2. `mqtt_listener.py` hands the payload to `decode_image.py`, which saves the
   image under a per-device folder and calls the API.
3. The API runs the snapshot through `SmartMeterReader`, which queries each
   engine and resolves a single value by consensus.
4. The reading is written to the meter's organization and shown on the
   dashboard with its history.

For the full picture, see [Technical Architecture](./docs/ARCHITECTURE.md) and
[Core Concepts](./docs/CONCEPTS.md).

## Tech stack

| Layer | Choice |
| --- | --- |
| API | FastAPI, SQLModel (SQLAlchemy + Pydantic v2) |
| Database | SQLite for development, PostgreSQL recommended for production |
| OCR / vision | Gemma 3, Qwen 2.5 VL, EasyOCR, Tesseract |
| Messaging | Eclipse Mosquitto (MQTT), paho-mqtt |
| Frontend | Vanilla JavaScript, HTML, CSS, Chart.js |
| Auth | OAuth2 password flow with JWT |

## Quick start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # needs tesseract-ocr on the host
cp .env.example .env.local

# Generate a JWT signing key and paste it into SECRET_KEY in .env.local
python -c "import secrets; print(secrets.token_urlsafe(64))"

uvicorn app.main:app --reload            # API + dashboard on http://localhost:8000
python mqtt_listener.py                  # optional: MQTT ingestion
```

Set `SECRET_KEY` before running anything you expose. If it is blank the app
generates a throwaway key at startup, which logs out every user on restart and
breaks under multiple workers.

To run the MQTT broker locally:

```bash
docker-compose up -d mqtt
```

## User roles

| Role | Scope | Can do |
| --- | --- | --- |
| Super Admin | Platform | Everything, including creating organizations and reading system logs |
| Platform Manager | Platform | Manage installers across organizations |
| Org Manager | Organization | Manage projects, assets, and users in their org |
| Org Viewer | Organization | Read-only access to their org |
| Installer | Organization | Install and validate meters in assigned orgs |

## Project status

The data model, RBAC, asset hierarchy, OCR ensemble, dashboard, and installer
UI are working. The install-time validation checks (field of view, glare,
reading confidence) currently run as a simulated scaffold rather than real
computer vision, and the ensemble returns a value but not yet a calibrated
confidence score. [Known Issues](./docs/KNOWN_ISSUES.md) tracks exactly what is
real, what is stubbed, and what is planned — read it before relying on a feature.

## Documentation

- [Core Concepts](./docs/CONCEPTS.md) — the model, multi-tenancy, and the OCR vote
- [Technical Architecture](./docs/ARCHITECTURE.md) — backend layout and data flow
- [Approach & Method](./docs/APPROACH.md) — design reasoning and how the code is maintained
- [Development Guidelines](./docs/GUIDELINES.md) — setup, conventions, security checklist
- [Knowledge Base](./docs/KNOWLEDGE_BASE.md) — gotchas worth knowing before changing deps, auth, or OCR
- [Known Issues](./docs/KNOWN_ISSUES.md) — current limitations
- [Changelog](./CHANGELOG.md)

## License

MIT. See [LICENSE](./LICENSE).
