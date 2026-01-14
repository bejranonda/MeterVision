"""Device/Camera models for hardware management."""
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from .base import TimestampMixin

if TYPE_CHECKING:
    from .tenant import Organization
    from .asset import Meter
    from .installation import InstallationSession



class CameraStatusEnum(str, Enum):
    """Camera status enumeration."""
    PROVISIONING = "provisioning"  # Initial registration
    ACTIVE = "active"              # Fully operational
    OFFLINE = "offline"            # No recent heartbeat
    FAILED = "failed"              # Installation validation failed
    DECOMMISSIONED = "decommissioned"  # Removed from service


class CameraBase(SQLModel):
    """Base camera attributes."""
    serial_number: str = Field(index=True, unique=True)
    organization_id: int = Field(foreign_key="organization.id")
    firmware_version: Optional[str] = None
    status: str = Field(default=CameraStatusEnum.PROVISIONING.value)
    meter_id: Optional[int] = Field(default=None, foreign_key="meter.id")


class Camera(CameraBase, TimestampMixin, table=True):
    """
    Camera/Device entity.
    
    Represents physical camera hardware installed for meter reading.
    Tracks lifecycle from provisioning through active operation.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    last_heartbeat: Optional[datetime] = None
    
    # Relationships
    organization: "Organization" = Relationship(back_populates="cameras")
    meter: Optional["Meter"] = Relationship(back_populates="camera")
    heartbeats: List["CameraHeartbeat"] = Relationship(back_populates="camera")
    installation_sessions: List["InstallationSession"] = Relationship(back_populates="camera")


class CameraHeartbeatBase(SQLModel):
    """Base heartbeat attributes."""
    camera_id: int = Field(foreign_key="camera.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    status_json: str = Field(default="{}")  # Flexible status data


class CameraHeartbeat(CameraHeartbeatBase, table=True):
    """
    Camera heartbeat log.
    
    Records periodic health checks from camera devices.
    Used to detect offline cameras and track connectivity.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    camera: Camera = Relationship(back_populates="heartbeats")
