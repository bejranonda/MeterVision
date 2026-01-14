"""Installation workflow models."""
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from .base import TimestampMixin

if TYPE_CHECKING:
    from .device import Camera
    from .asset import Meter
    from .user_rbac import User



class InstallationStatusEnum(str, Enum):
    """Installation session status."""
    STARTED = "started"
    CONNECTION_TEST_PASSED = "connection_test_passed"
    FOV_VALIDATED = "fov_validated"
    GLARE_CHECK_PASSED = "glare_check_passed"
    OCR_VALIDATED = "ocr_validated"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationTypeEnum(str, Enum):
    """Validation check types."""
    CONNECTION = "connection"
    FOV = "fov"              # Field of View
    GLARE = "glare"
    INITIAL_OCR = "initial_ocr"


class InstallationSessionBase(SQLModel):
    """Base installation session attributes."""
    camera_id: int = Field(foreign_key="camera.id")
    meter_id: int = Field(foreign_key="meter.id")
    installer_user_id: int = Field(foreign_key="user.id")
    organization_id: int = Field(foreign_key="organization.id")
    status: str = Field(default=InstallationStatusEnum.STARTED.value)


class InstallationSession(InstallationSessionBase, TimestampMixin, table=True):
    """
    Installation workflow session.
    
    Tracks the complete installation process from camera provisioning
    through validation to final activation.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    validation_results_json: str = Field(default="{}")  # Aggregated results
    
    # Relationships
    camera: "Camera" = Relationship(back_populates="installation_sessions")
    meter: "Meter" = Relationship(back_populates="installation_sessions")
    installer: "User" = Relationship(back_populates="installations")
    validation_checks: List["ValidationCheck"] = Relationship(back_populates="installation_session")


class ValidationCheckBase(SQLModel):
    """Base validation check attributes."""
    installation_session_id: int = Field(foreign_key="installationsession.id")
    check_type: str  # ValidationTypeEnum value
    status: str = Field(default="pending")  # pending, passed, failed
    result_json: str = Field(default="{}")  # Detailed check results


class ValidationCheck(ValidationCheckBase, TimestampMixin, table=True):
    """
    Individual validation check record.
    
    Each installation goes through multiple validation checks.
    This model tracks each check independently for audit trail.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    checked_at: Optional[datetime] = None
    
    # Relationships
    installation_session: InstallationSession = Relationship(back_populates="validation_checks")
