from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select, SQLModel
from typing import List, Optional
from datetime import timedelta
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
from .routers import organizations, installation
import os
import uuid
from dotenv import load_dotenv

load_dotenv(".env.local")

app = FastAPI(title="MeterVision Enterprise API")

# Include routers
app.include_router(organizations.router)
app.include_router(installation.router)

# Create uploads directory if not exists
os.makedirs("uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
    # Create default Super Admin user
    with next(get_session()) as session:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "securepassword123")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@metervision.local")
        hashed_pwd = get_password_hash(admin_password)
        
        user = session.exec(select(User).where(User.username == admin_username)).first()
        if not user:
            from .models import UserRoleEnum
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
                from .models import UserRoleEnum
                user.platform_role = UserRoleEnum.SUPER_ADMIN.value
            session.add(user)
            session.commit()
            print(f"✅ Updated Super Admin user: {admin_username}")


# Dependency
def get_db():
    from .database import get_session
    return next(get_session())

# Mount Static Files
app.mount("/static", StaticFiles(directory="/home/ogema/MeterReading/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("/home/ogema/MeterReading/static/index.html")

@app.get("/installer")
async def read_installer():
    """Serve the installer interface."""
    return FileResponse("/home/ogema/MeterReading/static/installer.html")

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

# --- Customers ---
@app.post("/customers/", response_model=Customer)
def create_customer(customer: CustomerBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_customer = Customer.from_orm(customer)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer

@app.get("/customers/", response_model=List[Customer])
def read_customers(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.exec(select(Customer)).all()

# --- Buildings ---
@app.post("/buildings/", response_model=Building)
def create_building(building: BuildingBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_building = Building.from_orm(building)
    session.add(db_building)
    session.commit()
    session.refresh(db_building)
    return db_building

@app.get("/buildings/", response_model=List[Building])
def read_buildings(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.exec(select(Building)).all()

# --- Places ---
@app.post("/places/", response_model=Place)
def create_place(place: PlaceBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_place = Place.from_orm(place)
    session.add(db_place)
    session.commit()
    session.refresh(db_place)
    return db_place

@app.get("/places/", response_model=List[Place])
def read_places(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.exec(select(Place)).all()

# --- Meters ---
@app.post("/meters/", response_model=Meter)
def create_meter(meter: MeterBase, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Create a new meter within an organization."""
    from .services.rbac_service import RBACService
    from .models import UserRoleEnum
    
    # Verify user has access to the organization
    user_role = RBACService.get_user_role_in_org(current_user.id, meter.organization_id, session)
    
    if not user_role and current_user.platform_role not in [UserRoleEnum.SUPER_ADMIN.value, UserRoleEnum.PLATFORM_MANAGER.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )
    
    db_meter = Meter.model_validate(meter)
    session.add(db_meter)
    session.commit()
    session.refresh(db_meter)
    return db_meter

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
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    upload_dir = "/home/ogema/MeterReading/uploads"
    file_path = os.path.join(upload_dir, filename)
    save_upload_file(file, file_path)
    
    # 3. Process Image
    reader = SmartMeterReader()
    reading_value = reader.read_meter(file_path, expected_value)
    
    # 4. Save Reading (with organization_id)
    reading = Reading(
        value=reading_value,
        raw_image_path=file_path,
        meter_id=meter.id,
        organization_id=meter.organization_id,  # Set from meter's organization
        status="Verified",
        ocr_confidence=1.0
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
