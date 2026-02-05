# 👁️ MeterVision **Enterprise Edition**

**Multi-Tenant B2B SaaS Platform for AI-Powered Meter Reading**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![OCR Ensemble](https://img.shields.io/badge/OCR-Ensemble-green)](https://github.com/tesseract-ocr/tesseract)
[![Gemma AI](https://img.shields.io/badge/Gemma-3--27B%20\u0026%2012B-blue?logo=google)](https://ai.google.dev/gemma)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-orange)](https://openrouter.ai/)

MeterVision is a comprehensive enterprise platform for offering "Meter Reading as a Service" to multiple organizations. It combines hierarchical asset management, AI-powered OCR, multi-tenancy, role-based access control, and camera-based installation workflows.

---

## 🌟 Enterprise Features

### 🏢 Multi-Tenant Architecture
- **Organization Management**: Support multiple customer organizations with complete data isolation
- **Role-Based Access Control (RBAC)**: 5 distinct user roles with granular permissions
- **Flexible User Assignment**: Users can belong to multiple organizations with different roles

### 👥 User Roles
1. **Super Admin** - Full system access, create organizations, view system logs
2. **Platform Manager** - Manage installers globally  
3. **Org Manager** - Manage specific organization, assign users
4. **Org Viewer** - Read-only access to organization data
5. **Installer** - Install and validate meters in assigned organizations

### 📦 Hierarchical Asset Management
Organize your infrastructure with a six-layer hierarchy:
- **Organization** → **Project** → **Customer** → **Building** → **Place** → **Meter**

All data is organization-scoped for multi-tenant isolation. Photos are automatically classified by device ID and stored by capture time.

### 📡 MQTT Snapshot Processing & Logging
- **Automated Processing**: Systems automatically listen for camera snapshots on MQTT topics.
- **Photo Classification**: Images are decoded from base64 and stored in device-specific folders (`uploads/<devMac>/`).
- **Comprehensive Logging**: Every MQTT message processing step is logged, including success status, file paths, and simulated meter readings.
- **Portal UI**: Dedicated 'Logs' section in the management portal for reviewing system activity and errors.

### 📷 Camera-Based Installation Workflow
- **QR Code Scanning**: Register cameras by scanning serial numbers
- **Validation Pipeline**: Multi-stage validation (connection → FOV → glare → OCR)
- **Heartbeat Monitoring**: Track camera connectivity and status
- **Installation Sessions**: Audit trail for every meter installation

### 🤖 Intelligent OCR Ensemble
MeterVision uses a sophisticated **voting ensemble** to ensure maximum accuracy:
1. **Google Gemma 3 27B & 12B**: State-of-the-art vision models (native and via OpenRouter)
2. **Qwen 2.5 VL**: Highly accurate visual-language model via OpenRouter
3. **EasyOCR**: Deep learning-based OCR for text extraction
4. **Tesseract OCR**: Industry standard for reliable processing
*Includes calibration system using expected values for improved confidence.*

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLModel (SQLAlchemy + Pydantic)
- **Database**: SQLite (dev), PostgreSQL (production recommended)
- **OCR Engine**: Tesseract, EasyOCR, Gemma 3, Qwen 2.5 VL
- **AI Providers**: Google AI Studio, OpenRouter
- **Frontend**: Vanilla JavaScript + Modern CSS
- **Icons**: Phosphor Icons
- **Authentication**: JWT with OAuth2 Password Flow

### Database Schema (15 Tables)
- **Tenant**: `organization`, `organizationsettings`
- **RBAC**: `user`, `userorganizationrole`  
- **Device**: `camera`, `cameraheartbeat`
- **Installation**: `installationsession`, `validationcheck`
- **Logging**: `log`
- **Assets**: `project`, `customer`, `building`, `place`, `meter`, `reading`

---

## ⚡ Quick Start

This project includes automated scripts to handle setup and deployment.

### 1. Initial Setup
First, run the setup script. This will check for prerequisites, create a Python virtual environment, install dependencies, and guide you through creating your `.env.local` configuration file.
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Deploy the Service
After the initial setup is complete, run the deployment script. This will configure and start the application as a systemd service, which runs in the background and starts automatically on boot.
```bash
chmod +x deploy.sh
./deploy.sh
```

The script will output the status and the URL where the application is accessible.

### 3. Verification
You can verify the installation and multi-tenant setup using the provided scripts:
```bash
python verify_setup.py         # Verify DB schema and OCR pipeline
python verify_installation.py  # Simulate end-to-end installation workflow
```

---

## ⚙️ Managing the Service

Once deployed as a systemd service, you can manage the MeterVision application using `systemctl` commands:

*   **Start the service:**
    ```bash
    sudo systemctl start metervision
    ```
*   **Stop the service:**
    ```bash
    sudo systemctl stop metervision
    ```
*   **Restart the service:**
    ```bash
    sudo systemctl restart metervision
    ```
*   **Check the status of the service:**
    ```bash
    sudo systemctl status metervision
    ```
*   **Enable the service (to start automatically on boot):**
    ```bash
    sudo systemctl enable metervision
    ```
*   **Disable the service (to prevent automatic start on boot):**
    ```bash
    sudo systemctl disable metervision
    ```
*   **Remove the service (uninstall):**
    ```bash
    sudo systemctl stop metervision
    sudo systemctl disable metervision
    sudo rm /etc/systemd/system/metervision.service
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ```
    Note: Removing the service does not remove the project files or database.

---

## 📖 API Endpoints

### Organization Management
```
POST   /api/organizations              # Create organization (Super Admin)
GET    /api/organizations               # List all organizations
GET    /api/organizations/my-organizations  # Get user's organizations
POST   /api/organizations/{id}/users    # Assign user to organization
GET    /api/organizations/{id}/users    # List organization users
```

### Asset Hierarchy
```
POST   /projects/                       # Create project
POST   /meters/                         # Create meter
GET    /meters_list/                    # List all meters (org-scoped)
POST   /meters/{serial}/reading         # Upload meter reading
```

### Installation (Complete)
```
POST   /api/installations/start         # Start installation session
POST   /api/installations/{id}/validate # Run validation pipeline
POST   /api/installations/cameras/heartbeat # Camera heartbeat webhook
```

### Logs
```
POST   /api/logs/                       # Create a new log entry (Internal)
GET    /api/logs/                       # Retrieve system logs
```

---

## 🔐 Security & Multi-Tenancy

### Data Isolation
- All entities include `organization_id` foreign key
- Queries automatically filtered by user's organization membership
- Super Admin can access all organizations

### Permission Enforcement
- Route-level permission checks via `PermissionChecker` middleware
- Organization context verification for all org-scoped routes
- Self-removal prevention (avoid accidental lockout)

### Recommended for Production
- Migrate to PostgreSQL with Row-Level Security (RLS)
- Enable audit logging for all mutations
- Implement API rate limiting
- Use API keys for camera heartbeat authentication

---

## 🧪 Verification & Testing

### Run Verification Script
```bash
python verify_setup.py  # Validates hierarchy creation and OCR pipeline
```

### Manual Testing via API Playground
1. Navigate to `http://localhost:8000/docs`
2. Click "Authorize" and login with Super Admin credentials
3. Create test organization: `POST /api/organizations`
4. Assign test users: `POST /api/organizations/{id}/users`
5. Verify data isolation between organizations

---

## 📊 Project Structure

```
MeterVision/
├── app/
│   ├── main.py              # Application entry, API routes
│   ├── database.py          # Database connection
│   ├── auth.py              # JWT authentication
│   ├── models/              # Multi-tenant data models
│   │   ├── tenant.py        # Organization models
│   │   ├── user_rbac.py     # User & RBAC
│   │   ├── device.py        # Camera models
│   │   ├── installation.py  # Installation workflow
│   │   ├── asset.py         # Asset hierarchy
│   │   └── log.py           # System logging
│   ├── middleware/
│   │   └── rbac.py          # Permission checking
│   ├── services/
│   │   ├── ocr.py           # SmartMeterReader (ensemble)
│   │   ├── rbac_service.py  # Organization/RBAC logic
│   │   └── log_service.py   # Logging logic
│   └── routers/
│       ├── organizations.py # Organization API
│       ├── installation.py  # Installation API
│       └── logs.py          # Logging API
├── static/                  # Frontend assets
├── uploads/                 # Meter images (organized by device)
├── logs/                    # Application logs
├── .env.local              # Environment configuration
└── requirements.txt         # Python dependencies
```

---

## 🚀 Roadmap

### ✅ Phase 1: Database Architecture (Complete)
- Multi-tenant schema with 14 tables
- Organization, User/RBAC, Camera, Installation models
- Organization-scoped asset hierarchy

### ✅ Phase 2: RBAC Implementation (Complete)
- Permission middleware and decorators
- Organization management APIs
- RBAC service layer

### ✅ Phase 3: Installer App Frontend (Complete)
- Mobile-first installer interface (`static/installer.html`)
- QR code scanner integration
- Installation wizard with validation progress
- Real-time API integration

### ✅ Phase 4: Validation Backend (Complete)
- Camera heartbeat service
- FOV, Glare, and OCR validation services
- Installation workflow orchestration logic
- Dedicated validation API endpoints

### ✅ Phase 5: Testing \u0026 Documentation (Complete)
- [Architecture \u0026 API Reference Guide](./reference/API.md)
- [Business Rules \u0026 Workflows](./business/RULES.md)
- Comprehensive simulation and verification scripts
- Multi-tenant and installation end-to-end tests

### ✅ Phase 6: MQTT Processing \u0026 Logging (Complete)
- Automated MQTT snapshot decoding and classification
- Multi-tenant logging system for audit trails
- Portal UI for system log monitoring

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## ⚖️ License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📚 Documentation

- [GEMINI.md](GEMINI.md) - Gemini AI context
- [CLAUDE.md](CLAUDE.md) - Claude AI context
- [Architecture & API Reference Guide](./reference/API.md)
- [Business Rules & Workflows](./business/RULES.md)