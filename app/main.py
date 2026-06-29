from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, SQLModel
from typing import List, Optional
from datetime import datetime, timedelta
from .database import create_db_and_tables, get_session
from .models import (
    # Asset hierarchy
    Project, ProjectBase, 
    Customer, CustomerBase, 
    Building, BuildingBase, 
    Place, PlaceBase, 
    Meter, MeterBase, 
    Reading, ReadingBase,
    # RBAC
    User,
    # Multi-tenant (imported for type hints, not used directly yet)
    Organization,
    UserOrganizationRole,
    Camera,
    InstallationSession,
    ValidationCheck
)
from .services.ocr import SmartMeterReader, save_upload_file
from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    create_access_token, 
    get_current_user, 
    verify_password,
    get_password_hash
)
from .routers import organizations, installation, logs
import os
import uuid
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware

load_dotenv(".env.local")

# Directory where uploaded meter images are stored. Configurable so the app is
# not tied to one developer's machine. Defaults to a relative "uploads" dir.
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, seed the Super Admin and default organization."""
    create_db_and_tables()

    # Create default Super Admin user
    with next(get_session()) as session:
        _seed_admin_and_org(session)
    yield


app = FastAPI(title="MeterVision Enterprise API", lifespan=lifespan)

# Add CORS Middleware. Allowed origins are configurable via CORS_ALLOW_ORIGINS
# (comma-separated); defaults cover the local companion frontend on port 8002.
_cors_origins = os.getenv(
    "CORS_ALLOW_ORIGINS", "http://localhost:8002,http://127.0.0.1:8002"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(organizations.router)
app.include_router(installation.router)
app.include_router(logs.router)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


def _seed_admin_and_org(session: Session):
    """Idempotently ensure the Super Admin user and default organization exist."""
    from .models import UserRoleEnum, Organization

    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "securepassword123")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@metervision.local")
    hashed_pwd = get_password_hash(admin_password)

    user = session.exec(select(User).where(User.username == admin_username)).first()
    if not user:
        user = User(
            username=admin_username,
            email=admin_email,
            full_name="System Administrator",
            hashed_password=hashed_pwd,
            platform_role=UserRoleEnum.SUPER_ADMIN.value,
            is_active=True
        )
        session.add(user)
        session.commit()
        print(f"✅ Created Super Admin user: {admin_username}")
    else:
        # Update existing user
        user.hashed_password = hashed_pwd
        user.email = admin_email
        if not user.platform_role:
            user.platform_role = UserRoleEnum.SUPER_ADMIN.value
        session.add(user)
        session.commit()
        print(f"✅ Updated Super Admin user: {admin_username}")

    # Ensure default organization exists
    default_org = session.exec(
        select(Organization).where(Organization.subdomain == "undefined")
    ).first()

    if not default_org:
        default_org = Organization(
            name="Undefined Organization",
            subdomain="undefined",
            is_active=True,
            billing_status="active"
        )
        session.add(default_org)
        session.commit()
        session.refresh(default_org)
        print(f"✅ Created default organization: Undefined Organization (ID: {default_org.id})")
    else:
        print(f"✅ Default organization exists: {default_org.name} (ID: {default_org.id})")


# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.get("/installer")
async def read_installer():
    """Serve the installer interface."""
    return FileResponse("static/installer.html")

# --- Auth ---
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Projects ---
@app.post("/projects/", response_model=Project)
def create_project(project: ProjectBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Create a new project within an organization."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    # Verify user has access to the organization
    user_role = RBACService.get_user_role_in_org(current_user.id, project.organization_id, session)
    
    if not user_role and current_user.platform_role not in [UserRoleEnum.SUPER_ADMIN.value, UserRoleEnum.PLATFORM_MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )
    
    db_project = Project.model_validate(project)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[Project])
def read_projects(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Get all projects accessible to the current user."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    # Super admin sees all projects
    if current_user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
        return list(session.exec(select(Project)).all())
    
    # Get user's organizations
    user_orgs = RBACService.get_user_organizations(current_user, session)
    org_ids = [org.id for org in user_orgs]
    
    if not org_ids:
        return []
    
    projects = session.exec(select(Project).where(Project.organization_id.in_(org_ids))).all()
    return list(projects)

# --- Org-scoping helpers ---
def _user_org_ids(current_user: User, session: Session) -> Optional[List[int]]:
    """Return the org IDs a user may access, or None for unrestricted (Super Admin)."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum

    if current_user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
        return None
    return [org.id for org in RBACService.get_user_organizations(current_user, session)]


def _assert_org_access(current_user: User, organization_id: int, session: Session):
    """Raise 403 unless the user may write to the given organization."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum

    if current_user.platform_role in [UserRoleEnum.SUPER_ADMIN.value, UserRoleEnum.PLATFORM_MANAGER.value]:
        return
    if not RBACService.get_user_role_in_org(current_user.id, organization_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )


# --- Customers ---
@app.post("/customers/", response_model=Customer)
def create_customer(customer: CustomerBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _assert_org_access(current_user, customer.organization_id, session)
    db_customer = Customer.model_validate(customer)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer

@app.get("/customers/", response_model=List[Customer])
def read_customers(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    org_ids = _user_org_ids(current_user, session)
    if org_ids is None:
        return list(session.exec(select(Customer)).all())
    if not org_ids:
        return []
    return list(session.exec(select(Customer).where(Customer.organization_id.in_(org_ids))).all())

# --- Buildings ---
@app.post("/buildings/", response_model=Building)
def create_building(building: BuildingBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _assert_org_access(current_user, building.organization_id, session)
    db_building = Building.model_validate(building)
    session.add(db_building)
    session.commit()
    session.refresh(db_building)
    return db_building

@app.get("/buildings/", response_model=List[Building])
def read_buildings(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    org_ids = _user_org_ids(current_user, session)
    if org_ids is None:
        return list(session.exec(select(Building)).all())
    if not org_ids:
        return []
    return list(session.exec(select(Building).where(Building.organization_id.in_(org_ids))).all())

# --- Places ---
@app.post("/places/", response_model=Place)
def create_place(place: PlaceBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _assert_org_access(current_user, place.organization_id, session)
    db_place = Place.model_validate(place)
    session.add(db_place)
    session.commit()
    session.refresh(db_place)
    return db_place

@app.get("/places/", response_model=List[Place])
def read_places(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    org_ids = _user_org_ids(current_user, session)
    if org_ids is None:
        return list(session.exec(select(Place)).all())
    if not org_ids:
        return []
    return list(session.exec(select(Place).where(Place.organization_id.in_(org_ids))).all())

# --- Meters ---
@app.post("/meters/", response_model=Meter)
def create_meter(meter: MeterBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Create a new meter within an organization."""
    from .models import Organization

    # Use default organization if none specified
    org_id = meter.organization_id
    if not org_id:
        default_org = session.exec(
            select(Organization).where(Organization.subdomain == "undefined")
        ).first()
        org_id = default_org.id if default_org else 1

    # Verify user has access to the organization
    _assert_org_access(current_user, org_id, session)

    # Create meter with resolved organization_id
    meter_dict = meter.model_dump()
    meter_dict['organization_id'] = org_id
    db_meter = Meter(**meter_dict)
    session.add(db_meter)
    session.commit()
    session.refresh(db_meter)
    return db_meter

@app.delete("/meters/{meter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meter(meter_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Delete a meter."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    meter = session.get(Meter, meter_id)
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
        
    # Verify user has access to the organization
    user_role = RBACService.get_user_role_in_org(current_user.id, meter.organization_id, session)
    
    # Allow Super Admin, Platform Manager, or Org Manager to delete
    if not (current_user.platform_role in [UserRoleEnum.SUPER_ADMIN.value, UserRoleEnum.PLATFORM_MANAGER.value] or 
            user_role == UserRoleEnum.ORG_MANAGER.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this meter"
        )
    
    session.delete(meter)
    session.commit()
    return None

@app.get("/meters_list/", response_model=List[Meter])
def read_all_meters(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Get all meters accessible to the current user."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    # Super admin sees all meters
    if current_user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
        return list(session.exec(select(Meter)).all())
    
    # Get user's organizations
    user_orgs = RBACService.get_user_organizations(current_user, session)
    org_ids = [org.id for org in user_orgs]
    
    if not org_ids:
        return []
    
    meters = session.exec(select(Meter).where(Meter.organization_id.in_(org_ids))).all()
    return list(meters)

@app.get("/meters/{serial_number}", response_model=Meter)
def read_meter_by_serial(serial_number: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Get a meter by serial number (must belong to user's organization)."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    meter = session.exec(select(Meter).where(Meter.serial_number == serial_number)).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    # Check if user has access to this meter's organization
    if current_user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
        return meter
    
    user_orgs = RBACService.get_user_organizations(current_user, session)
    org_ids = [org.id for org in user_orgs]
    
    if meter.organization_id not in org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this meter's organization"
        )
    
    return meter

# --- Readings ---
@app.post("/meters/{serial_number}/reading", response_model=Reading)
async def upload_reading(
    serial_number: str, 
    file: UploadFile = File(...), 
    expected_value: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Upload a meter reading with OCR processing."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    # 1. Verify Meter Exists and user has access
    meter = session.exec(select(Meter).where(Meter.serial_number == serial_number)).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    # Check organization access
    if current_user.platform_role != UserRoleEnum.SUPER_ADMIN.value:
        user_orgs = RBACService.get_user_organizations(current_user, session)
        org_ids = [org.id for org in user_orgs]
        
        if meter.organization_id not in org_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this meter's organization"
            )
    
    # 2. Save Image
    file_ext = (file.filename or "").rsplit(".", 1)[-1] or "jpg"
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    save_upload_file(file, file_path)

    # 3. Process Image
    reader = SmartMeterReader()
    reading_value = reader.read_meter(file_path, expected_value, meter.custom_prompt)

    # 4. Save Reading (with organization_id)
    # The ensemble returns 0.0 when every engine failed to read a value; reflect
    # that honestly instead of marking every reading "Verified" with full
    # confidence. If the expected value was provided and matched, we trust it.
    matched_expected = False
    if expected_value:
        try:
            matched_expected = reading_value == float(str(expected_value).replace(",", "."))
        except (TypeError, ValueError):
            matched_expected = False
    verified = bool(reading_value and reading_value > 0)
    reading = Reading(
        value=reading_value,
        raw_image_path=file_path,
        meter_id=meter.id,
        organization_id=meter.organization_id,  # Set from meter's organization
        status="Verified" if verified else "Failed",
        ocr_confidence=1.0 if matched_expected else (0.7 if verified else 0.0)
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)
    return reading

class ReadingCreate(SQLModel):
    value: float
    timestamp: datetime
    image_path: str

@app.post("/meters/{serial_number}/reading_data", response_model=Reading)
def create_reading_data(
    serial_number: str, 
    reading_data: ReadingCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a reading record directly (for edge devices that already processed the image).
    """
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    # 1. Verify Meter Exists
    meter = session.exec(select(Meter).where(Meter.serial_number == serial_number)).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    # Check organization access
    if current_user.platform_role != UserRoleEnum.SUPER_ADMIN.value:
        user_orgs = RBACService.get_user_organizations(current_user, session)
        org_ids = [org.id for org in user_orgs]
        
        if meter.organization_id not in org_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this meter's organization"
            )

    # 2. Save Reading
    reading = Reading(
        value=reading_data.value,
        timestamp=reading_data.timestamp,
        raw_image_path=reading_data.image_path,
        meter_id=meter.id,
        organization_id=meter.organization_id,
        status="Verified",
        ocr_confidence=1.0 # Assumed high confidence from edge
    )
    session.add(reading)
    session.commit()
    session.refresh(reading)
    return reading

@app.get("/meters/{serial_number}/readings", response_model=List[Reading])
def read_readings(serial_number: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    meter = session.exec(select(Meter).where(Meter.serial_number == serial_number)).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    return session.exec(select(Reading).where(Reading.meter_id == meter.id).order_by(Reading.timestamp.desc())).all()

# --- Meter Configuration ---
class MeterUpdate(SQLModel):
    aoi_config: Optional[str] = None

@app.patch("/meters/{serial_number}", response_model=Meter)
def update_meter_config(serial_number: str, update_data: MeterUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    statement = select(Meter).where(Meter.serial_number == serial_number)
    results = session.exec(statement)
    meter = results.first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    if update_data.aoi_config is not None:
        meter.aoi_config = update_data.aoi_config
        
    session.add(meter)
    session.commit()
    session.refresh(meter)
    return meter
