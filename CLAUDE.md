# MeterVision Enterprise Context for Claude

## Project Overview
MeterVision is a comprehensive B2B SaaS platform for offering "Meter Reading as a Service" to multiple organizations. It features multi-tenant architecture, role-based access control (RBAC), AI-powered OCR ensemble, and camera-based installation workflows with validation.

### Key Technologies
- **Backend:** Python 3.10+, FastAPI, SQLModel (SQLAlchemy + Pydantic)
- **Database:** SQLite (dev), PostgreSQL (production recommended)
- **AI/OCR:** Google Gemma 3 (27B \u0026 12B), Qwen 2.5 VL, EasyOCR, Tesseract OCR
- **Frontend:** Vanilla JavaScript, HTML5, CSS3, Phosphor Icons
- **Authentication:** OAuth2 with Password Flow (JWT)
- **Architecture:** Multi-tenant with organization-scoped data isolation

## Architecture & Structure
The project follows a modular FastAPI structure with multi-tenant support:

```
/home/ogema/MeterReading/
├── app/
│   ├── main.py              # Application entry, API routes, startup
│   ├── database.py          # Database connection, session management
│   ├── auth.py              # JWT authentication logic
│   ├── models/              # Multi-tenant data models (15 tables)
│   │   ├── base.py          # TimestampMixin, SoftDeleteMixin
│   │   ├── tenant.py        # Organization, OrganizationSettings
│   │   ├── user_rbac.py     # User, UserOrganizationRole, UserRoleEnum
│   │   ├── device.py        # Camera, CameraHeartbeat, CameraStatusEnum
│   │   ├── installation.py  # InstallationSession, ValidationCheck
│   │   ├── asset.py         # Project, Customer, Building, Place, Meter, Reading
│   │   └── log.py           # System logs
│   ├── middleware/
│   │   └── rbac.py          # PermissionChecker, get_current_user_org_context
│   ├── services/
│   │   ├── ocr.py           # SmartMeterReader (ensemble voting mechanism)
│   │   ├── rbac_service.py  # RBACService, OrganizationService
│   │   └── log_service.py   # Logging service
│   └── routers/
│       ├── organizations.py # Organization management API
│       ├── installation.py  # Installation workflow API
│       └── logs.py          # System logging API
├── static/                  # Frontend assets (served via /static)
│   ├── app.js               # SPA logic
│   ├── index.html           # Main entry point
│   └── style.css            # Styling
├── logs/                    # Application logs
├── uploads/                 # Storage for uploaded meter images (by device)
├── verify_setup.py          # Integration testing script
└── requirements.txt         # Python dependencies
```

## Multi-Tenant Data Model

### Hierarchy
1. **Organization**: Top-level tenant entity (B2B customers)
2. **Project**: Top-level container within an organization
3. **Customer**: Clients or tenants
4. **Building**: Physical assets
5. **Place**: Locations within buildings (e.g., "Basement")
6. **Meter**: The physical device (supports Electricity, Gas, Heat)
7. **Reading**: Historical data points linked to meters (includes image path)

### Additional Entities
- **User**: Enhanced with email, platform_role, full_name
- **UserOrganizationRole**: Junction table for user-organization-role mapping
- **Camera**: Device registry for meter reading cameras
- **CameraHeartbeat**: Connectivity logs
- **InstallationSession**: Tracks installation workflow
- **ValidationCheck**: Individual validation step results
- **Log**: System-wide event logging

### Multi-Tenant Isolation Strategy
- All entities include `organization_id` foreign key for data isolation
- Queries filtered by user's organization membership via middleware
- Super Admin can access all organizations
- Indexes on `organization_id` for query performance

## Role-Based Access Control (RBAC)

### User Roles
```python
class UserRoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"           # Full system access, log access
    PLATFORM_MANAGER = "platform_manager" # Manage installers globally  
    ORG_MANAGER = "org_manager"           # Manage specific organization
    ORG_VIEWER = "org_viewer"             # Read-only org access
    INSTALLER = "installer"                # Install and validate meters
```

### Permission Model
- **Platform Roles**: Stored in `User.platform_role` (SUPER_ADMIN, PLATFORM_MANAGER)
- **Organization Roles**: Stored in `UserOrganizationRole` junction table
- **Multi-Org Users**: Installers can be assigned to multiple organizations with different roles
- **Permission Middleware**: `PermissionChecker` dependency class for route protection

## Setup & Execution

### Prerequisites
- Python 3.10+
- Tesseract OCR installed (`apt install tesseract-ocr`)

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Create `.env.local` file in the root directory:
```env
GEMINI_API_KEY=your_google_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=securepassword123
ADMIN_EMAIL=admin@metervision.local
```

### Running the Application (Dev)
```bash
uvicorn app.main:app --reload
python mqtt_listener.py
```

### Running as Services (Service-First Approach)
The application is designed to run as managed `systemd` services on the host for better integration with local hardware and AI APIs.

```bash
# Backend API
systemctl status metervision

# MQTT Gateway
systemctl status metervision-mqtt
```

### MQTT Broker (Containerized)
The `mosquitto` broker is the only component that requires a container in the standard setup.
```bash
docker-compose up -d mqtt
```

### Verification
```bash
python verify_setup.py  # Validates hierarchy creation and OCR pipeline
```

## Development Conventions

### Backend
- **Dependency Injection:** Uses `Depends(get_session)` for database access and `Depends(get_current_user)` for protected routes
- **Multi-Tenant Queries:** All org-scoped routes use `get_current_user_org_context` to verify access
- **OCR Logic:** `SmartMeterReader` class in `app/services/ocr.py` implements voting system with Gemma 3 27B (Google), Gemma 3 12B (OpenRouter), and Qwen 2.5 VL (OpenRouter), prioritizing their agreement or corroborating with EasyOCR and Tesseract
- **File Handling:** Uploads saved to `uploads/<device_mac>/` directory
- **Service Layer:** Business logic separated into `app/services/` for testability

### RBAC Middleware
```python
# Route protection example:
from app.middleware import PermissionChecker
from app.models import UserRoleEnum

@app.get("/admin-only")
def admin_route(
    checker: PermissionChecker = Depends(
        PermissionChecker(require_role=[UserRoleEnum.SUPER_ADMIN])
    )
):
    pass

# Organization context verification:
from app.middleware import get_current_user_org_context

@app.get("/organizations/{org_id}/data")
async def get_org_data(org_id: int, ...):
    user, org = await get_current_user_org_context(org_id, current_user, session)
    # user has verified access to org
```

### Frontend
- **SPA Architecture:** Modern sidebar-based UI with client-side routing in `app.js`
- **Auth:** Stores JWT in `localStorage`
- **Logging Portal:** Dedicated UI for viewing system logs and MQTT processing results

### Common Tasks
- **Adding a new model:** Update `app/models/*.py` and run the app (SQLModel automatically creates tables)
- **Creating new API router:** Create file in `app/routers/`, include in `main.py` with `app.include_router()`
- **Adding RBAC to route:** Use `PermissionChecker` dependency or `require_super_admin` / `require_platform_manager` helpers
- **Tweaking OCR:** Modify `SmartMeterReader` in `app/services/ocr.py` to adjust confidence thresholds or voting logic

## Installation Workflow (Phase 4 - Complete)

### Workflow States
```python
STARTED → CONNECTION_TEST_PASSED → FOV_VALIDATED  
  → GLARE_CHECK_PASSED → OCR_VALIDATED → COMPLETED
```

### Validation Types
- **CONNECTION**: Camera heartbeat verification
- **FOV**: Field of View check (meter fully visible)
- **GLARE**: Glare/lighting detection
- **INITIAL_OCR**: OCR reading confidence check

### Camera Statuses
- **PROVISIONING**: Initial registration
- **ACTIVE**: Fully operational
- **OFFLINE**: No recent heartbeat
- **FAILED**: Installation validation failed
- **DECOMMISSIONED**: Removed from service

## API Endpoints

### Organization Management
```
POST   /api/organizations                    # Create org (Super Admin only)
GET    /api/organizations                     # List all orgs (Platform Manager+)
GET    /api/organizations/my-organizations    # Get user's orgs
GET    /api/organizations/{id}                # Get org details
POST   /api/organizations/{id}/users          # Assign user to org
GET    /api/organizations/{id}/users          # List org users
DELETE /api/organizations/{id}/users/{user_id}  # Remove user
```

### Asset Hierarchy (Complete)
```
POST   /projects/                      # Create project
POST   /customers/                     # Create customer
POST   /buildings/                     # Create building
POST   /places/                        # Create place
POST   /meters/                        # Create meter
GET    /meters_list/                   # List meters (needs org-scoping)
POST   /meters/{serial}/reading        # Upload reading
```

### Installation (Phase 4 - Complete)
```
POST   /api/installations/start              # Start installation session
POST   /api/installations/{id}/validate      # Run validation pipeline
GET    /api/installations/{id}/status        # Get installation status
POST   /api/installations/{id}/complete      # Complete installation
POST   /api/cameras/heartbeat                # Camera heartbeat webhook
```

### Logs (New)
```
POST   /api/logs/                            # Create a new log entry (Internal)
GET    /api/logs/                            # Retrieve system logs
```

## Current Implementation Status

### ✅ Phase 1: Database Architecture (Complete)
- Multi-tenant schema with 15 tables
- Organization, User/RBAC, Camera, Installation, Log models
- Organization-scoped data isolation
- Migrations and TYPE_CHECKING for circular imports

### ✅ Phase 2: RBAC Implementation (Complete)
- Permission middleware (`PermissionChecker`)
- Organization management APIs
- RBAC service layer (`RBACService`, `OrganizationService`)
- Super Admin auto-creation on startup

### ✅ Phase 3: Installer Frontend (Complete)
- Mobile-first installer interface (`static/installer.html`)
- QR code scanner integration
- Installation wizard UI with validation feedback
- API integration for complete workflow

### ✅ Phase 4: Validation Backend (Complete)
- Camera service (status tracking, simulated heartbeat)
- Validation service (FOV, glare, OCR - simulated integration ready)
- Installation workflow orchestration (start -> validate -> complete)
- Installation API endpoints with RBAC

### ✅ Phase 5: Testing & Documentation (Complete)
- Created verification scripts (`verify_setup.py`, `verify_installation.py`)
- Comprehensive architecture documentation
- Unit test pattern established

### ✅ Phase 6: MQTT Processing & Logging (Complete)
- Automated MQTT snapshot decoding and classification
- Multi-tenant logging system for audit trails
- Portal UI for system log monitoring

## Migration Notes

### Breaking Changes from v0.1
- `User` model enhanced with `email`, `platform_role`, `full_name`
- All asset entities now require `organization_id`
- Models reorganized into `app/models/` package (old `models.py` backed up as `models_old.py`)
- New dependency: Organization context required for most routes

### Migration Path for Existing Data
```sql
-- Create default organization
INSERT INTO organization (name, subdomain, is_active, billing_status)
VALUES ('Legacy Organization', 'legacy', 1, 'active');

-- Assign organization to existing projects
UPDATE project SET organization_id = (SELECT id FROM organization WHERE subdomain = 'legacy');

-- Upgrade existing admin user
UPDATE user 
SET platform_role = 'super_admin', 
    email = 'admin@metervision.local'
WHERE username = 'admin';
```

## Security Considerations

- **Data Isolation**: All queries filtered by organization_id
- **Permission Enforcement**: Route-level checks via middleware
- **Super Admin Bypass**: Explicit checks prevent accidental permission bugs
- **Self-Removal Prevention**: Users cannot remove themselves from organizations
- **Production Recommendations**:
  - Migrate to PostgreSQL with Row-Level Security (RLS)
  - Enable audit logging
  - Implement API rate limiting
  - Use API keys for camera heartbeat authentication

## Development Workflow

1. **Create new feature branch**
2. **Update models** if schema changes required
3. **Implement service layer** business logic
4. **Create API router** with RBAC protection
5. **Update frontend** if needed
6. **Write tests** for new functionality
7. **Update documentation** (README, context files)
8. **Submit PR** with comprehensive description

## Troubleshooting

### Database Issues
- Delete `meter_reading.db` and restart server to recreate schema
- Check SQLModel echo logs for query debugging

### RBAC Issues
- Verify user has correct platform_role or UserOrganizationRole assignment
- Check `get_current_user_org_context` for access denial reasons

### Import Errors
- Ensure all model files use `TYPE_CHECKING` for forward references
- Check `app/models/__init__.py` exports all required symbols
