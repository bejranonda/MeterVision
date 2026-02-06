# MeterVision Technical Architecture

## 🏛️ System Overview
MeterVision is a modular FastAPI application designed for high scalability and secure multi-tenancy.

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

## 📡 MQTT Integration
For cameras that transmit via MQTT:
- **Base64 Decoding**: Snapshots are received as base64 strings.
- **Automated Filing**: Images are stored in `/uploads/{camera_serial}/{timestamp}.jpg`.
- **Async Processing**: Incoming snapshots trigger OCR processing in the background.

## 🔌 API Philosophy
- **RESTful**: standard HTTP verbs (GET, POST, PATCH, DELETE).
- **JWT Auth**: Every org-scoped request must include a Bearer token.
- **Scoped Responses**: The backend ensures that even if an ID is guessed, the user cannot see data outside their tenant.
