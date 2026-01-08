# MeterVision Context for Gemini

## Project Overview
MeterVision is a robust, end-to-end solution designed to manage complex meter infrastructures and automate the process of collecting readings through advanced computer vision. It utilizes a hierarchical asset management system and an "OCR Ensemble" approach combining local OCR engines with Google's Gemini AI.

### Key Technologies
- **Backend:** Python 3.10+, FastAPI, SQLModel (SQLAlchemy + Pydantic)
- **Database:** SQLite (default: `meter_reading.db`), extensible to PostgreSQL.
- **AI/OCR:** Google Gemini 3 Flash, EasyOCR, Tesseract OCR.
- **Frontend:** Vanilla JavaScript, HTML5, CSS3, Phosphor Icons (no build step required).
- **Authentication:** OAuth2 with Password Flow (JWT).

## Architecture & Structure
The project follows a standard FastAPI structure:

```
D:\Git\Werapol\MeterVision\
├── app\
│   ├── main.py           # Application entry point, API routes, App config
│   ├── models.py         # SQLModel database schemas (Hierarchy: Project > ... > Meter)
│   ├── database.py       # Database connection and session management
│   ├── auth.py           # JWT authentication logic
│   └── services\
│       └── ocr.py        # SmartMeterReader logic (Ensemble voting mechanism)
├── static\               # Frontend assets (served via /static)
│   ├── app.js            # SPA logic
│   ├── index.html        # Main entry point
│   └── style.css         # Styling
├── logs\                 # Application logs
├── uploads\              # Storage for uploaded meter images
├── verify_setup.py       # Integration testing script
└── requirements.txt      # Python dependencies
```

### Data Model (Hierarchy)
1.  **Project**: Top-level container.
2.  **Customer**: Clients or tenants.
3.  **Building**: Physical assets.
4.  **Place**: Locations within buildings (e.g., "Basement").
5.  **Meter**: The physical device (supports Electricity, Gas, Heat).
6.  **Reading**: Historical data points linked to meters (includes image path).

## Setup & Execution

### Prerequisites
*   Python 3.10+
*   Tesseract OCR installed on the system (e.g., `apt install tesseract-ocr` or Windows installer).

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Create a `.env.local` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword123
```

### Running the Application
To start the development server:
```bash
uvicorn app.main:app --reload
```
- **Dashboard:** `http://localhost:8000/`
- **API Docs:** `http://localhost:8000/docs`

### Verification
Run the verification script to validate the hierarchy creation and OCR pipeline:
```bash
python verify_setup.py
```

## Development Conventions

### Backend
- **Dependency Injection:** Uses `Depends(get_session)` for database access and `Depends(get_current_user)` for protected routes.
- **OCR Logic:** The `SmartMeterReader` class in `app/services/ocr.py` implements a voting system. It prioritizes Gemini for complex tasks but falls back to or corroborates with EasyOCR and Tesseract.
- **File Handling:** Uploads are saved to the `uploads/` directory. **Note:** Ensure paths are handled relatively using `os.path` to avoid OS-specific hardcoding issues.

### Frontend
- **Lightweight:** Pure HTML/JS. `state` object in `app.js` manages simple SPA routing and data.
- **Auth:** Stores JWT in `localStorage`.

### Common Tasks
- **Adding a new model:** Update `app/models.py` and run the app (SQLModel automatically creates tables if they don't exist on startup).
- **Tweaking OCR:** Modify `SmartMeterReader` in `app/services/ocr.py` to adjust confidence thresholds or voting logic.
