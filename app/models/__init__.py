# Models package - Multi-tenant enterprise architecture
from .base import TimestampMixin, SoftDeleteMixin
from .tenant import Organization, OrganizationRead, OrganizationSettings, OrganizationBase, OrganizationSettingsBase
from .user_rbac import User, UserRoleEnum, UserOrganizationRole, UserBase, UserOrganizationRoleBase
from .device import Camera, CameraHeartbeat, CameraStatusEnum, CameraBase, CameraHeartbeatBase
from .installation import (
    InstallationSession, ValidationCheck, 
    InstallationStatusEnum, ValidationTypeEnum,
    InstallationSessionBase, ValidationCheckBase
)
from .asset import (
    Project, Customer, Building, Place, Meter, Reading,
    ProjectBase, CustomerBase, BuildingBase, PlaceBase, MeterBase, ReadingBase
)
from .log import Log, LogCreate, LogRead

# For backward compatibility, export all at package level
__all__ = [
    # Base mixins
    "TimestampMixin",
    "SoftDeleteMixin",
    # Tenant models
    "Organization",
    "OrganizationRead",
    "OrganizationSettings",
    "OrganizationBase",
    "OrganizationSettingsBase",
    # RBAC models
    "User",
    "UserRoleEnum",
    "UserOrganizationRole",
    "UserBase",
    "UserOrganizationRoleBase",
    # Device models
    "Camera",
    "CameraHeartbeat",
    "CameraStatusEnum",
    "CameraBase",
    "CameraHeartbeatBase",
    # Installation models
    "InstallationSession",
    "ValidationCheck",
    "InstallationStatusEnum",
    "ValidationTypeEnum",
    "InstallationSessionBase",
    "ValidationCheckBase",
    # Asset hierarchy models
    "Project",
    "Customer",
    "Building",
    "Place",
    "Meter",
    "Reading",
    "ProjectBase",
    "CustomerBase",
    "BuildingBase",
    "PlaceBase",
    "MeterBase",
    "ReadingBase",
    # Log models
    "Log",
    "LogCreate",
    "LogRead",
]

