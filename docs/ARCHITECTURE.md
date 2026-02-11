# MeterVision Technical Architecture

## 🏛️ System Overview
MeterVision is a coordinated ecosystem of services working together to provide real-time meter reading and management.

### Platform Components
- **API Backend**: FastAPI application serving the dashboard and mobile installer.
- **IoT Listener**: Python-based MQTT subscriber for capturing device data.
- **MQTT Broker**: Eclipse Mosquitto (Docker-based) for device communication.
- **Database**: SQLModel/SQLite (mapped to PostgreSQL in production).

## 🏗️ Backend Structure
The backend is organized into functional layers:
- **Routers**: Handle HTTP requests and entry points.
- **Services**: Contain business logic (OCR, RBAC, Installation orchestration).
- **Models**: SQLModel (SQLAlchemy + Pydantic) definitions for the database.
- **Middleware**: Intercepts requests for authentication and tenant-based permission checks.

## 🗄️ Database Architecture
The system uses a 15-table relational schema (SQLite for development, PostgreSQL recommended for production).

### Key Table Groups:
- **Tenancy**: `organization`, `organizationsettings`
- **Security**: `user`, `userorganizationrole` (junction table)
- **Infrastructure**: `camera`, `meter`, `project`
- **Data**: `reading`, `log`
- **Workflow**: `installationsession`, `validationcheck`

## 🧠 AI Voting Logic (SmartMeterReader)
Located in `app/services/ocr.py`, the `SmartMeterReader` class coordinates the ensemble:

1.  **Image Preprocessing**: Handles decoding and optimization.
2.  **Parallel Inference**: Calls Google AI Studio (Gemma) and OpenRouter (Qwen) APIs.
3.  **Local Corroboration**: Runs EasyOCR or Tesseract locally for immediate confirmation.
4.  **Voting Algorithm**: 
    - If Gemma and Qwen agree -> Confirmed.
    - If they disagree, use the local OCR or expected value to break the tie.

## 🖥️ Frontend Architecture
MeterVision uses a **"Modern Vanilla"** approach to front-end development:
- **No Heavy Frameworks**: Pure HTML5, CSS3, and JavaScript (ES6+).
- **SPA Behavior**: Uses `app.js` with a custom router and template-based rendering for a fast, responsive feel without the complexity of React/Vue.
- **Design System**: A custom CSS-variable-based theme (Glassmorphism) that supports both mobile and desktop seamlessly.
- **Data Visualization**: Integrated `Chart.js` for real-time historic data plotting.

## 📡 MQTT Gateway & IoT Workflow
The `metervision-mqtt` service acts as the bridge between physical sensors and the AI backend.

### Communication Flow:
1.  **Device Trigger**: An IoT camera (e.g., NE101) takes a photo and publishes to `NE101SensingCam/Snapshot`.
2.  **Listener Capture**: `mqtt_listener.py` receives the payload (usually Base64 encoded).
3.  **Decoding**: The payload is passed to `decode_image.py` which validates the image and saves it to a tenant-scoped directory in `/uploads/`.
4.  **Backend Notification**: The snapshot event is logged, and the backend is notified to perform OCR analysis.

### Infrastructure:
- **Broker**: Runs as a Docker container (`eclipse-mosquitto:2`) with local volume persistence for logs and data.
- **Topics**: 
  - `v1/devices/me/telemetry`: Device health and status.
  - `NE101SensingCam/Snapshot`: Binary/Base64 image data.

## 🔌 API Philosophy
- **RESTful**: standard HTTP verbs (GET, POST, PATCH, DELETE).
- **JWT Auth**: Every org-scoped request must include a Bearer token.
- **Scoped Responses**: The backend ensures that even if an ID is guessed, the user cannot see data outside their tenant.
