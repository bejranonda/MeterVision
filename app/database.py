from sqlmodel import SQLModel, create_engine, Session

# Import all models to ensure they're registered with SQLModel
from .models import (
    # Base
    TimestampMixin, SoftDeleteMixin,
    # Tenant
    Organization, OrganizationSettings,
    # RBAC
    User, UserOrganizationRole,
    # Device
    Camera, CameraHeartbeat,
    # Installation
    InstallationSession, ValidationCheck,
    # Asset hierarchy
    Project, Customer, Building, Place, Meter, Reading
)

sqlite_file_name = "meter_reading.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    """Create all tables based on SQLModel metadata."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Database session dependency."""
    with Session(engine) as session:
        yield session
