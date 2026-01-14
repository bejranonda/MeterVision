# 👁️ MeterVision **Enterprise Edition**

**Multi-Tenant B2B SaaS Platform for AI-Powered Meter Reading**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![OCR Ensemble](https://img.shields.io/badge/OCR-Ensemble-green)](https://github.com/tesseract-ocr/tesseract)
[![Gemini AI](https://img.shields.io/badge/Gemini-1.5%20\u0026%202.0%20Flash-violet?logo=google-gemini)](https://deepmind.google/technologies/gemini/)

MeterVision is a comprehensive enterprise platform for offering "Meter Reading as a Service" to multiple organizations. It combines hierarchical asset management, AI-powered OCR, multi-tenancy, role-based access control, and camera-based installation workflows.

---

## 🌟 Enterprise Features

### 🏢 Multi-Tenant Architecture
- **Organization Management**: Support multiple customer organizations with complete data isolation
- **Role-Based Access Control (RBAC)**: 5 distinct user roles with granular permissions
- **Flexible User Assignment**: Users can belong to multiple organizations with different roles

### 👥 User Roles
1. **Super Admin** - Full system access, create organizations
2. **Platform Manager** - Manage installers globally  
3. **Org Manager** - Manage specific organization, assign users
4. **Org Viewer** - Read-only access to organization data
5. **Installer** - Install and validate meters in assigned organizations

### 📦 Hierarchical Asset Management
Organize your infrastructure with a six-layer hierarchy:
- **Organization** → **Project** → **Customer** → **Building** → **Place** → **Meter**

All data is organization-scoped for multi-tenant isolation.

### 📷 Camera-Based Installation Workflow
- **QR Code Scanning**: Register cameras by scanning serial numbers
- **Validation Pipeline**: Multi-stage validation (connection → FOV → glare → OCR)
- **Heartbeat Monitoring**: Track camera connectivity and status
- **Installation Sessions**: Audit trail for every meter installation

### 🤖 Intelligent OCR Ensemble
MeterVision uses a sophisticated **voting ensemble** to ensure maximum accuracy:
1. **Google Gemini 1.5 & 2.0 Flash**: State-of-the-art vision-language models
2. **EasyOCR**: Deep learning-based OCR for text extraction
3. **Tesseract OCR**: Industry standard for reliable processing
*Includes calibration system using expected values for improved confidence.*

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLModel (SQLAlchemy + Pydantic)
- **Database**: SQLite (dev), PostgreSQL (production recommended)
- **OCR Engine**: Tesseract, EasyOCR, Google Gemini
- **Frontend**: Vanilla JavaScript + Modern CSS
- **Icons**: Phosphor Icons
- **Authentication**: JWT with OAuth2 Password Flow

### Database Schema (14 Tables)
- **Tenant**: `organization`, `organizationsettings`
- **RBAC**: `user`, `userorganizationrole`  
- **Device**: `camera`, `cameraheartbeat`
- **Installation**: `installationsession`, `validationcheck`
- **Assets**: `project`, `customer`, `building`, `place`, `meter`, `reading`

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+
- Tesseract OCR installed (`sudo apt install tesseract-ocr`)

### 2. Installation
```bash
git clone https://github.com/bejranonda/MeterVision.git
cd MeterVision
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Create `.env.local` in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword123
ADMIN_EMAIL=admin@metervision.local
```

### 4. Run
```bash
uvicorn app.main:app --reload
```

Visit:
- **Dashboard**: `http://localhost:8000`
- **Installer App**: `http://localhost:8000/installer`
- **API Docs**: `http://localhost:8000/docs`

On first startup, a Super Admin user is auto-created with credentials from `.env.local`.

### 5. Verification
Verify the installation and multi-tenant setup:
```bash
python verify_setup.py         # Verify DB schema and OCR pipeline
python verify_installation.py  # Simulate end-to-end installation workflow
```

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

### Installation (Coming in Phase 3-4)
```
POST   /api/installations/start         # Start installation session
POST   /api/installations/{id}/validate # Run validation pipeline
POST   /api/cameras/heartbeat           # Camera heartbeat webhook
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
│   │   └── asset.py         # Asset hierarchy
│   ├── middleware/
│   │   └── rbac.py          # Permission checking
│   ├── services/
│   │   ├── ocr.py           # SmartMeterReader (ensemble)
│   │   └── rbac_service.py  # Organization/RBAC logic
│   └── routers/
│       └── organizations.py # Organization API
├── static/                  # Frontend assets
├── uploads/                 # Meter images
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

### 🔄 Phase 5: Testing & Documentation (In Progress)
- [Architecture & API Reference Guide](./reference/API.md)
- [Business Rules & Workflows](./business/RULES.md)
- Simulation and verification scripts
- Unit and integration test suite expansion

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## ⚖️ License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📚 Documentation

- [Implementation Plan](docs/implementation_plan.md) - Technical specification
- [Research & Validation](docs/research_validation.md) - Testing strategy
- [Walkthrough](docs/walkthrough.md) - Phase 1-2 completion report
- [GEMINI.md](GEMINI.md) - Gemini AI context
- [CLAUDE.md](CLAUDE.md) - Claude AI context
